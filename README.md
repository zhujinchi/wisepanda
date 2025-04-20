# Fratcher：Bamboo Slip Fragment Matcher Based on WisePanda


Fratcher is an intuitive computer-assisted tool that implements WisePanda’s capabilities in a practical workflow.Based on physics of fracture and deterioration process,WisePanda predicts matching probabilities among fragments and offers archaeologists a ranked list of the top potential matches for each fragment.Compared to the leading curve matching method, WisePanda increases Top-20 matching accuracy from 35% to 69%. Archaeologists using WisePanda have experienced substantial efficiency improvements (20 times faster) when rejoining fragmented bamboo slips.

![img.png](img.png)

## Key Features


- First physics-driven deep learning framework designed for rejoining fragmented ancient bamboo slips
- Achieves high accuracy compared with vision model
- Handles both fracture pattern generation and material degradation simulation
- Establishes a new paradigm for fragment matching where training data is scarce.
- Combines physical principles with artificial intelligence
- Intuitive GUI for selection, comparison, and verification integrated AI-assistant

## Quik Start Guide


### 1.Installation

```
# Create and activate conda environment
conda create -n fratcher python=3.11
conda activate fratcher

# Install requirements
pip install -r requirements.txt

# Install full version Qfluentwidgets
pip install "PyQt6-Fluent-Widgets[full]" -i https://pypi.org/simple/
```
### 2.Launch Fratcher
```
python demo.py
```


