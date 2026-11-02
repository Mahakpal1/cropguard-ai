import numpy as np
import pytest
from PIL import Image

from cv import estimate, level_for
from tests.conftest import leaf_image


@pytest.mark.parametrize("pct,lvl", [(0, "Mild"), (9.9, "Mild"), (10, "Moderate"), (34.9, "Moderate"), (35, "Severe"), (80, "Severe")])
def test_level_bins(pct, lvl):
    assert level_for(pct) == lvl


@pytest.mark.parametrize("frac,lvl", [(0.0, "Mild"), (0.05, "Mild"), (0.30, "Moderate"), (0.50, "Severe")])
def test_severity_estimate_tracks_area(frac, lvl):
    r = estimate(leaf_image(frac))
    assert r["level"] == lvl
    assert abs(r["affected_pct"] - frac * 100) < 3
    assert r["leaf_fraction"] > 0.9


def test_blank_background_has_no_leaf():
    r = estimate(Image.fromarray(np.full((200, 200, 3), 235, np.uint8)))
    assert r["leaf_fraction"] < 0.02 and r["affected_pct"] == 0.0


def test_custom_bins():
    assert estimate(leaf_image(0.30), bins=(40, 60))["level"] == "Mild"


def test_return_masks_shapes():
    r, leaf, les = estimate(leaf_image(0.2), return_masks=True)
    assert leaf.shape == les.shape and les.sum() <= leaf.sum()
