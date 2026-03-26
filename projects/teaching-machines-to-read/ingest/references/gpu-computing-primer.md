# GPU Computing Primer

A plain-language guide to GPU computing concepts relevant to this project, written for grant applications and technical discussions.

## What a GPU Is

A computer has two main processors:

- **CPU** (Central Processing Unit) — the "brain" of the computer. Great at doing one thing at a time, very fast. Handles normal tasks: opening apps, browsing the web, writing documents.
- **GPU** (Graphics Processing Unit) — originally designed to render images and video. Can do thousands of simple calculations at the same time, in parallel. A CPU is one brilliant mathematician; a GPU is a stadium full of decent mathematicians who all work simultaneously.

## Why AI Models Need GPUs

Training or fine-tuning an AI model is a massive math problem. The model looks at thousands of images, compares its guesses against correct answers, and adjusts itself — over and over, millions of times. A CPU would take weeks or months. A GPU does it in hours or days because it runs calculations in parallel.

**VRAM** (Video RAM) is the GPU's dedicated memory — its workspace. For fine-tuning TrOCR, we need at least **16 GB of VRAM**. This is enough room to hold the model and the training data being processed at any given moment.

## How Researchers Access GPUs

Most personal laptops either don't have a GPU or have one that's too small for AI training. Researchers use GPUs that live somewhere else:

- **Cloud GPUs** — Companies like Google, Amazon, and NVIDIA rent out powerful GPUs over the internet. You connect from your laptop, run your training job on their hardware, and get results back. Google Colab and Kaggle provide this for free.
- **University clusters** — Institutions like CUNY's High Performance Computing Center maintain buildings full of powerful GPU-equipped computers that students can use remotely. You submit a job (e.g., "train this model on this data"), it runs on their hardware, and you retrieve the results.

In both cases, the laptop acts as a remote control for a much more powerful machine elsewhere.

## Key Terms for Grant Applications

| Term | What It Means |
|------|--------------|
| **GPU compute time** / **GPU resources** | The thing you're requesting — access to run jobs on a GPU |
| **Fine-tuning a pre-trained model** | Taking an existing trained model and teaching it a new, specific task. Much cheaper than training from scratch. |
| **Pre-trained model** | A model that has already learned general patterns (e.g., how to read modern handwriting) and can be adapted to a new task (e.g., early modern secretary hand) |
| **NVIDIA T4** | A specific GPU model commonly available for free (Google Colab, Kaggle). 16 GB VRAM. Sufficient for TrOCR fine-tuning. |
| **NVIDIA A100** | A more powerful GPU available through university clusters and grants. 40-80 GB VRAM. |
| **VRAM** | Video RAM — the GPU's dedicated memory. 16 GB minimum for this project. |
| **Mixed-precision training (fp16)** | A technique that cuts memory usage by ~30% by using lower-precision numbers where full precision isn't needed. Makes training fit on smaller GPUs. |
| **LoRA / QLoRA** | Parameter-efficient fine-tuning methods that update only a small fraction of the model's parameters, further reducing GPU memory requirements to as little as 8-12 GB VRAM. |
| **Batch size** | How many training examples the GPU processes at once. Larger = faster but needs more memory. For our project, batch size 8-16 on a T4. |
| **Epoch** | One complete pass through all the training data. Fine-tuning typically takes 10-30 epochs. |
| **Inference** | Using a trained model to make predictions (as opposed to training it). Requires less GPU power. |

## Sample Language for Grant Proposals

### Describing the computing need:

> This project requires GPU compute time to fine-tune a pre-trained handwriting recognition model (Microsoft TrOCR) on paired manuscript images and transcriptions from the Folger Shakespeare Library. We estimate approximately 20-40 hours of GPU time on an NVIDIA T4 or equivalent for initial model training, with additional time for iterative refinement.

### Describing the technical approach:

> We will fine-tune Microsoft's open-source TrOCR model — a transformer-based encoder-decoder architecture for handwritten text recognition — on a corpus of paired manuscript images and semi-diplomatic transcriptions of early modern English recipe books. The base model, pre-trained on modern handwriting recognition, will be adapted to recognize early modern English secretary hand (c. 1550-1700) using parameter-efficient fine-tuning techniques (LoRA) to minimize computational requirements. The resulting model will be published as an open-source resource on HuggingFace for use by other researchers.

### Describing the gap being filled:

> While handwritten text recognition models exist for medieval Latin and continental European scripts (e.g., TRIDIS, Transkribus), no open-source model currently exists for early modern English secretary hand — the script used in the vast majority of English manuscripts from the 16th and 17th centuries, including recipe books, letters, legal documents, and literary manuscripts. This project aims to fill that gap by producing a freely available, open-source model trained specifically on English recipe manuscript hands from the Folger Shakespeare Library's collection.
