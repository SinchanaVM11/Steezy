# Pretrained model-provider evaluation

**Date:** 2026-09-27  
**Scope:** Fashion perception and image embeddings only. Vector retrieval and
Inspiration are out of scope.

## Current baseline audit

`VisualFeatureEmbedding` is a deterministic 36-dimensional RGB histogram plus
2×2 spatial-pool feature. It is image-derived and normalized, but it has no
learned semantic representation. `DeterministicFashionPerception` uses the
filename only for category labels, extracts a simple dominant color, and
returns `unknown` rather than fabricating attributes or confidence. These are
useful contract and preprocessing baselines, not garment perception models.

The local environment has PyTorch, torchvision, Transformers, and ONNX
Runtime, but no FashionCLIP, DINOv2, Wargon, or other candidate weights
available as a complete pinned artifact. The cached OpenAI CLIP directory was
not treated as a validated deployment artifact. No network download, model
execution, or secret is required by this evaluation.

## Reproducible criteria

Candidates were compared on:

1. **Fashion relevance:** evidence of fashion-domain training or useful
   transfer to garment images.
2. **Output fit:** image embedding dimension, normalization support, and
   whether garment classification is available without inventing labels.
3. **Offline reproducibility:** immutable weight/config/processor snapshot,
   explicit revision, and no runtime Hub/network dependency.
4. **Deployment/licensing clarity:** model-card warnings, weight/data terms,
   and artifact provenance.
5. **Evaluation evidence:** published or reproducible in-domain metrics,
   taxonomy fit, and known image-distribution limitations.
6. **Integration cost:** compatibility with the existing
   `EmbeddingService`/`PerceptionService` protocols and CPU memory/latency
   expectations.

Any future provider must pass a fixed local fixture gate: exact artifact
revision, preprocessing configuration, output dimension, finite normalized
vector, repeatability, explicit provenance, and a labeled garment benchmark
covering category and unknown/abstention behavior. A model must not become the
default based only on generic ImageNet or zero-shot claims.

## Candidate comparison

| Candidate | Fashion relevance | Embedding / perception | Offline and license assessment | Decision |
|---|---|---|---|---|
| **FashionCLIP 2.0** (`patrickjohncyh/fashion-clip`) | Highest. Fine-tuned on approximately 800K Farfetch fashion image/text pairs; model card reports weighted macro-F1 improvements over OpenAI CLIP on FMNIST, KAGL, and DEEP. | ViT-B/32, 512-D image/text projection; supports text-prompt zero-shot classification but has no fixed garment head. | Can be loaded from a pinned local Transformers snapshot. The model card states it was not developed for deployment and notes bias toward centered, white-background product images. The current card declares MIT, but upstream data/provenance and deployment suitability still require review. | **Best future candidate; do not integrate yet.** |
| **OpenAI CLIP ViT-B/32** (`openai/clip-vit-base-patch32`) | General image/text representation; weaker fashion specificity and known fine-grained limitations. | 512-D image/text embedding; prompt-based classification, no garment head. | MIT code/weights and local checkpoint loading are clear, but the model card recommends in-domain testing and warns against assuming broad deployment suitability. | Baseline comparator only. |
| **OpenCLIP / LAION ViT-B/32** | Broad ecosystem and stronger checkpoint choices than original CLIP; fashion relevance depends on checkpoint. | Usually 512-D for ViT-B/32; zero-shot classification and embeddings. Dimension and preprocessing are checkpoint-specific. | Software is MIT, but pretrained checkpoint/data terms vary. LAION data is uncurated and the candidate card warns that deployment is out of scope. | Not selected until exact checkpoint and terms are pinned. |
| **DINOv2-S/B** (`facebookresearch/dinov2`) | Strong generic visual features; not fashion-trained and requires a fashion classifier/probe for categories. | Embeddings only: 384-D (S) or 768-D (B); no garment taxonomy or text prompts. | Apache-2.0 model/repository and local snapshot path are comparatively clear. Still needs a labeled fashion probe and benchmark. | Good generic fallback; not sufficient for this milestone’s perception goal. |
| **Wargon clothing classifier** (`wargoninnovation/wargon-clothing-classifier`) | Direct secondhand-clothing classifier with 27 fixed categories and reported validation accuracy around 73%. | ViT-Base/16 classifier; probabilities for its fixed labels, but no general embedding representation. | Apache-2.0 model card and local Transformers loading. Limited taxonomy and product-image distribution; cannot cover Steezy’s unknown/open-world requirements without an abstention evaluation. | Useful optional classifier experiment, not a unified provider. |

Primary sources:

- FashionCLIP model card and reported comparisons:
  <https://huggingface.co/patrickjohncyh/fashion-clip>
- FashionCLIP repository:
  <https://github.com/patrickjohncyh/fashion-clip>
- OpenAI CLIP repository/model card:
  <https://github.com/openai/CLIP>
- OpenAI CLIP Transformers configuration (512 projection):
  <https://huggingface.co/openai/clip-vit-base-patch32>
- OpenCLIP repository:
  <https://github.com/mlfoundations/open_clip>
- DINOv2 repository/model card:
  <https://github.com/facebookresearch/dinov2>
- Wargon classifier model card:
  <https://huggingface.co/wargoninnovation/wargon-clothing-classifier>

## Decision

Do **not** replace the current provider in this milestone. FashionCLIP 2.0 is
the recommended next experiment because it best matches the fashion embedding
requirement and exposes a 512-dimensional multimodal space. The evidence is
not sufficient to ship it as a default: the exact weight snapshot is not
present locally, deployment is explicitly cautioned against, the training
distribution is product-centric, and Steezy has no checked-in labeled
benchmark for user-uploaded images.

No pretrained provider was implemented, no model weights were downloaded, and
no endpoint or persistence contract changed. The existing provider protocols
remain ready for an opt-in local implementation.

## Required next experiment before implementation

1. Obtain approval for the exact FashionCLIP revision and model/data terms.
2. Vendor or cache the complete snapshot (weights, config, processor/tokenizer)
   outside Git, record its SHA/revision, and enforce offline loading.
3. Build a small representative, consented, local evaluation set with
   category labels, unknown/out-of-taxonomy examples, and varied backgrounds.
4. Compare FashionCLIP 2.0, OpenAI CLIP, and the current baseline on:
   category macro-F1, abstention/unknown behavior, embedding repeatability,
   same-item vs different-item cosine separation, CPU latency, memory, and
   artifact size.
5. Only then add a provider adapter that emits 512-D normalized vectors,
   records model/revision/preprocessing provenance, and leaves confidence null
   unless calibrated by the benchmark.

The current milestone intentionally stops before vector storage, nearest
neighbor search, recommendation, and Inspiration UI.
