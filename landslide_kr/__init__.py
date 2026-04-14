"""
landslide_kr — Korea Landslide Nowcasting Framework

Inspired by wildfire_kr architecture. Couples:
- Physically-based shallow landslide models (SHALSTAB, TRIGRS, SINMAP)
- GEE-based data collection (GPM rainfall, Sentinel-1 InSAR, Dynamic World, WorldCover)
- Korean event labels (NIDR, 재해연보, Sentinel-2 post-event mapping)
- Ensemble parameter sweep + probability maps
- Validation metrics (IoU, Precision, Recall, F1 on landslide/non-landslide cells)

Core modules:
- models/: SHALSTAB, TRIGRS, SINMAP implementations or wrappers
- collectors/: GEE + KMA + NIDR data pipelines
- io/: Case config, raster I/O, label readers
- viz/: Susceptibility maps, ROC curves
"""

__version__ = "0.1.0-scaffold"
__all__ = ["models", "collectors", "io", "viz"]
