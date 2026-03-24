# lahgtna-chatterbox


**Lahgtna** is an Arabic speech AI project focused on building
**dialect-aware Text-to-Speech (TTS)** systems.\
The goal of the project is to improve Arabic speech generation while
preserving natural speaking styles and expressive audio.

------------------------------------------------------------------------

## Hugging Face Model

The Lahgtna model is available on Hugging Face:

`https://huggingface.co/oddadmix/lahgtna-chatterbox-v1`

You can download the model, explore training details, and run inference
directly through the Hugging Face ecosystem.

------------------------------------------------------------------------

## Supported Dialects

| Code | Dialect       | Chatterbox language |
|------|---------------|---------------------|
| `eg` | Egyptian      | `ms`                |
| `sa` | Saudi         | `sv`                |
| `mo` | Moroccan      | `pl`                |
| `iq` | Iraqi         | `no`                |
| `sd` | Sudanese      | `pt`                |
| `tn` | Tunisian      | `da`                |
| `lb` | Lebanese      | `nl`                |
| `sy` | Syrian        | `ko`                |
| `ly` | Libyan        | `sw`                |
| `ps` | Palestinian   | `he`                |
| `ar` | MSA (default) | `ar`                |

> **Note:** Non-Arabic ISO codes in the *Chatterbox language* column are
> repurposed backbone identifiers — this is intentional.


### Reference audio

Place your speaker reference `.wav` / `.flac` files in `./wavs/`.
The expected filenames are listed in `config.LANGUAGE_CODES`.  You can
provide your own recordings — any clean, 3–10 second mono clip at ≥ 22 kHz
will work.

---

## Quick start

```bash
python inference.py \
  --text "اه ياراسي الواحد دماغه وجعاه" \
  --output output.wav
```

Override dialect detection:

```bash
python inference.py \
  --text "يا هلا والله" \
  --dialect sa \
  --output saudi.wav
```

Adjust generation parameters:

```bash
python inference.py \
  --text "..." \
  --exaggeration 0.9 \
  --temperature 0.7 \
  --cfg-weight 0.4
```

## Fine-Tuning

The repository currently includes a **fine-tuning script** that allows
training the model on datasets.



## Training

The dataset should contain atleast 3 columns `audio` `text` and `language`

We are using the existing languages in Chatterbox and overriding them for Arabic dialects. This way we avoid adding new tokens and resizing the embeddings of the model.

To fine‑tune the model:

``` bash
python finetune.py --output_dir ./checkpoints/eg-sa-ma-iq-v1 --model_name_or_path oddadmix/lahgtna-chatterbox-v0 --dataset_name oddadmix/example --train_split_name train --eval_split_size 0.005 --num_train_epochs 1 --per_device_train_batch_size 4 --gradient_accumulation_steps 2 --learning_rate 5e-5 --warmup_steps 100 --logging_steps 10 --eval_strategy steps --eval_steps 400 --save_strategy steps --save_steps 100 --save_total_limit 2 --fp16 True --report_to wandb --dataloader_num_workers 8 --do_train --do_eval --dataloader_pin_memory False --eval_on_start True --label_names labels_speech --text_column_name text
```


------------------------------------------------------------------------

## Goal

Lahgtna aims to advance:

-   Arabic speech synthesis
-   Dialect-aware speech models
-   Open research for Arabic speech technology
