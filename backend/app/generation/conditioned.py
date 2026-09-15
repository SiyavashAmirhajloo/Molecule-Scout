"""Seed-graph init: start reverse diffusion from a noised retrieved molecule.

The V4 checkpoint is unconditional (task_type=[]), so there is no condition
encoder to inject guidance vectors into. Instead we convert the retrieved
molecule to its graph, forward-noise it to step t_int, and denoise from there.
t_int is the knob: small = near-copy of the seed, large = near-unconditioned.
"""

import random

import numpy as np
import torch
import torch.nn.functional as F
from torch_geometric.loader import DataLoader

from app.chem.embeddings import parse_smiles

RETRIEVAL_CONDITION_MIN_TANIMOTO = 0.3


def seed_graph(model, seed_smiles: str):
    from torch_molecule.generator.graph_dit.utils import to_dense

    mol = parse_smiles(seed_smiles)
    if mol is None:
        raise ValueError(f"Invalid seed SMILES: {seed_smiles!r}")
    graphs = model._convert_to_pytorch_data([seed_smiles])
    batch = next(iter(DataLoader(graphs, batch_size=1, shuffle=False)))
    active = model.dataset_info["active_index"]
    x = F.one_hot(batch.x, num_classes=118).float()[:, active]
    e = F.one_hot(batch.edge_attr, num_classes=5).float()
    dense, node_mask = to_dense(x, batch.edge_index, e, batch.batch, model.max_node)
    return dense, node_mask


def forward_noise(model, dense, node_mask, t_int: int):
    from torch_molecule.generator.graph_dit.diffusion import sample_discrete_features

    bs, n = 1, model.max_node
    alpha_bar = model.noise_schedule.get_alpha_bar(t_int=torch.full((bs, 1), t_int))
    qtb = model.transition_model.get_Qt_bar(alpha_bar, model.device)
    joined = torch.cat([dense.X, dense.E.reshape(bs, n, -1)], dim=-1)
    prob = joined @ qtb.X
    px = prob[:, :, : model.input_dim_X]
    pe = prob[:, :, model.input_dim_X :].reshape(bs, n, n, -1)
    sampled = sample_discrete_features(probX=px, probE=pe, node_mask=node_mask)
    x = F.one_hot(sampled.X, num_classes=model.input_dim_X).float()
    e = F.one_hot(sampled.E, num_classes=model.input_dim_E).float()
    return x, e


def denoise_from(model, x, e, node_mask, t_int: int):
    t_total = model.timesteps
    for s_int in reversed(range(t_int)):
        s = torch.full((1, 1), s_int / t_total)
        t = torch.full((1, 1), (s_int + 1) / t_total)
        out = model.sample_p_zs_given_zt(s, t, x, e, None, node_mask)
        x, e = out.X, out.E
    return out


def generate_seeded(
    model, seed_smiles: str, n: int, noise_steps: int = 100, seed: int | None = None
) -> list[str]:
    from torch_molecule.utils import graph_to_smiles

    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
    model.model.eval()
    dense, node_mask = seed_graph(model, seed_smiles)
    k = int(node_mask.sum())
    decoder = model.dataset_info["atom_decoder"]
    out = []
    with torch.no_grad():
        for _ in range(n):
            x, e = forward_noise(model, dense, node_mask, noise_steps)
            final = denoise_from(model, x, e, node_mask, noise_steps)
            collapsed = final.mask(node_mask, collapse=True)
            smiles = graph_to_smiles(
                [[collapsed.X[0, :k].cpu(), collapsed.E[0, :k, :k].cpu()]], decoder
            )[0]
            if smiles:
                out.append(smiles)
    return out
