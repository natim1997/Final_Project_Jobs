---
tags:
- sentence-transformers
- sentence-similarity
- feature-extraction
- generated_from_trainer
- dataset_size:8000
- loss:CosineSimilarityLoss
base_model: sentence-transformers/paraphrase-multilingual-mpnet-base-v2
widget:
- source_sentence: 'Job Category: אפסנאות ולוגיסטיקה, Company: TechCorp, Salary: 67
    per hour, Hours: 08:00-17:00, Requirements: Experience in the field, Ability to
    work in shifts. Location: Tel Aviv, Contact: 050-1234567.'
  sentences:
  - 'Candidate Details: Name: 1338, Address: Tel Aviv, Search Radius: 18km, Skills:
    Excel, Java, Soft Skills: Team player, Fast learner. Looking for הפקה ואירועים
    job.'
  - 'Candidate Details: Name: 2857, Address: Tel Aviv, Search Radius: 6km, Skills:
    Java, Driving License, Soft Skills: Team player, Fast learner. Looking for משלוחים
    ותחבורה job.'
  - 'Candidate Details: Name: 8802, Address: Tel Aviv, Search Radius: 21km, Skills:
    Java, English, Soft Skills: Team player, Fast learner. Looking for מכירות ואופנה
    job.'
- source_sentence: 'Job Category: בניין וייצור, Company: TechCorp, Salary: 41 per
    hour, Hours: 08:00-17:00, Requirements: Experience in the field, Ability to work
    in shifts. Location: Tel Aviv, Contact: 050-1234567.'
  sentences:
  - 'Candidate Details: Name: 6305, Address: Tel Aviv, Search Radius: 9km, Skills:
    English, Excel, Soft Skills: Team player, Fast learner. Looking for רפואה ורווחה
    job.'
  - 'Candidate Details: Name: 2067, Address: Tel Aviv, Search Radius: 21km, Skills:
    Driving License, Python, Soft Skills: Team player, Fast learner. Looking for עיצוב
    וקריאייטיב job.'
  - 'Candidate Details: Name: 4482, Address: Tel Aviv, Search Radius: 18km, Skills:
    Java, English, Soft Skills: Team player, Fast learner. Looking for אבטחה וביטחון
    job.'
- source_sentence: 'Job Category: רפואה ורווחה, Company: TechCorp, Salary: 40 per
    hour, Hours: 08:00-17:00, Requirements: Experience in the field, Ability to work
    in shifts. Location: Tel Aviv, Contact: 050-1234567.'
  sentences:
  - 'Candidate Details: Name: 9021, Address: Tel Aviv, Search Radius: 8km, Skills:
    Driving License, Excel, Soft Skills: Team player, Fast learner. Looking for אפסנאות
    ולוגיסטיקה job.'
  - 'Candidate Details: Name: 8178, Address: Tel Aviv, Search Radius: 8km, Skills:
    Driving License, English, Soft Skills: Team player, Fast learner. Looking for
    רפואה ורווחה job.'
  - 'Candidate Details: Name: 3774, Address: Tel Aviv, Search Radius: 23km, Skills:
    Python, Driving License, Soft Skills: Team player, Fast learner. Looking for בעלי
    חיים job.'
- source_sentence: 'Job Category: טכנולוגיה, Company: TechCorp, Salary: 31 per hour,
    Hours: 08:00-17:00, Requirements: Experience in the field, Ability to work in
    shifts. Location: Tel Aviv, Contact: 050-1234567.'
  sentences:
  - 'Candidate Details: Name: 4136, Address: Tel Aviv, Search Radius: 20km, Skills:
    Python, Excel, Soft Skills: Team player, Fast learner. Looking for אחזקה job.'
  - 'Candidate Details: Name: 9111, Address: Tel Aviv, Search Radius: 27km, Skills:
    SAP, English, Soft Skills: Team player, Fast learner. Looking for בניין וייצור
    job.'
  - 'Candidate Details: Name: 3494, Address: Tel Aviv, Search Radius: 28km, Skills:
    SAP, Python, Soft Skills: Team player, Fast learner. Looking for טכנולוגיה job.'
- source_sentence: 'Job Category: בניין וייצור, Company: TechCorp, Salary: 50 per
    hour, Hours: 08:00-17:00, Requirements: Experience in the field, Ability to work
    in shifts. Location: Tel Aviv, Contact: 050-1234567.'
  sentences:
  - 'Candidate Details: Name: 7656, Address: Tel Aviv, Search Radius: 14km, Skills:
    English, SAP, Soft Skills: Team player, Fast learner. Looking for מסעדנות job.'
  - 'Candidate Details: Name: 6539, Address: Tel Aviv, Search Radius: 12km, Skills:
    Java, English, Soft Skills: Team player, Fast learner. Looking for מסעדנות job.'
  - 'Candidate Details: Name: 1627, Address: Tel Aviv, Search Radius: 13km, Skills:
    Driving License, Excel, Soft Skills: Team player, Fast learner. Looking for בניין
    וייצור job.'
pipeline_tag: sentence-similarity
library_name: sentence-transformers
---

# SentenceTransformer based on sentence-transformers/paraphrase-multilingual-mpnet-base-v2

This is a [sentence-transformers](https://www.SBERT.net) model finetuned from [sentence-transformers/paraphrase-multilingual-mpnet-base-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2). It maps sentences & paragraphs to a 768-dimensional dense vector space and can be used for retrieval.

## Model Details

### Model Description
- **Model Type:** Sentence Transformer
- **Base model:** [sentence-transformers/paraphrase-multilingual-mpnet-base-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2) <!-- at revision 4328cf26390c98c5e3c738b4460a05b95f4911f5 -->
- **Maximum Sequence Length:** 256 tokens
- **Output Dimensionality:** 768 dimensions
- **Similarity Function:** Cosine Similarity
- **Supported Modality:** Text
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/huggingface/sentence-transformers)
- **Hugging Face:** [Sentence Transformers on Hugging Face](https://huggingface.co/models?library=sentence-transformers)

### Full Model Architecture

```
SentenceTransformer(
  (0): Transformer({'transformer_task': 'feature-extraction', 'modality_config': {'text': {'method': 'forward', 'method_output_name': 'last_hidden_state'}}, 'module_output_name': 'token_embeddings', 'architecture': 'XLMRobertaModel'})
  (1): Pooling({'embedding_dimension': 768, 'pooling_mode': 'mean', 'include_prompt': True})
)
```

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```
Then you can load this model and run inference.
```python
from sentence_transformers import SentenceTransformer

# Download from the 🤗 Hub
model = SentenceTransformer("sentence_transformers_model_id")
# Run inference
sentences = [
    'Job Category: בניין וייצור, Company: TechCorp, Salary: 50 per hour, Hours: 08:00-17:00, Requirements: Experience in the field, Ability to work in shifts. Location: Tel Aviv, Contact: 050-1234567.',
    'Candidate Details: Name: 6539, Address: Tel Aviv, Search Radius: 12km, Skills: Java, English, Soft Skills: Team player, Fast learner. Looking for מסעדנות job.',
    'Candidate Details: Name: 1627, Address: Tel Aviv, Search Radius: 13km, Skills: Driving License, Excel, Soft Skills: Team player, Fast learner. Looking for בניין וייצור job.',
]
embeddings = model.encode(sentences)
print(embeddings.shape)
# [3, 768]

# Get the similarity scores for the embeddings
similarities = model.similarity(embeddings, embeddings)
print(similarities)
# tensor([[1.0000, 0.0019, 0.9993],
#         [0.0019, 1.0000, 0.0027],
#         [0.9993, 0.0027, 1.0000]])
```
<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 8,000 training samples
* Columns: <code>sentence_0</code>, <code>sentence_1</code>, and <code>label</code>
* Approximate statistics based on the first 100 samples:
  |          | sentence_0                                                                         | sentence_1                                                                        | label                                                         |
  |:---------|:-----------------------------------------------------------------------------------|:----------------------------------------------------------------------------------|:--------------------------------------------------------------|
  | type     | string                                                                             | string                                                                            | float                                                         |
  | modality | text                                                                               | text                                                                              |                                                               |
  | details  | <ul><li>min: 59 tokens</li><li>mean: 61.12 tokens</li><li>max: 65 tokens</li></ul> | <ul><li>min: 47 tokens</li><li>mean: 50.1 tokens</li><li>max: 56 tokens</li></ul> | <ul><li>min: 0.0</li><li>mean: 0.5</li><li>max: 1.0</li></ul> |
* Samples:
  | sentence_0                                                                                                                                                                                                           | sentence_1                                                                                                                                                                        | label            |
  |:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------|
  | <code>Job Category: עיצוב וקריאייטיב, Company: TechCorp, Salary: 44 per hour, Hours: 08:00-17:00, Requirements: Experience in the field, Ability to work in shifts. Location: Tel Aviv, Contact: 050-1234567.</code> | <code>Candidate Details: Name: 2926, Address: Tel Aviv, Search Radius: 29km, Skills: Java, Driving License, Soft Skills: Team player, Fast learner. Looking for אחזקה job.</code> | <code>0.0</code> |
  | <code>Job Category: בעלי חיים, Company: TechCorp, Salary: 49 per hour, Hours: 08:00-17:00, Requirements: Experience in the field, Ability to work in shifts. Location: Tel Aviv, Contact: 050-1234567.</code>        | <code>Candidate Details: Name: 9110, Address: Tel Aviv, Search Radius: 28km, Skills: Python, SAP, Soft Skills: Team player, Fast learner. Looking for בעלי חיים job.</code>       | <code>1.0</code> |
  | <code>Job Category: בעלי חיים, Company: TechCorp, Salary: 57 per hour, Hours: 08:00-17:00, Requirements: Experience in the field, Ability to work in shifts. Location: Tel Aviv, Contact: 050-1234567.</code>        | <code>Candidate Details: Name: 2278, Address: Tel Aviv, Search Radius: 30km, Skills: SAP, English, Soft Skills: Team player, Fast learner. Looking for בעלי חיים job.</code>      | <code>1.0</code> |
* Loss: [<code>CosineSimilarityLoss</code>](https://sbert.net/docs/package_reference/sentence_transformer/losses.html#cosinesimilarityloss) with these parameters:
  ```json
  {
      "loss_fct": "torch.nn.modules.loss.MSELoss",
      "cos_score_transformation": "torch.nn.modules.linear.Identity"
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `per_device_train_batch_size`: 16
- `num_train_epochs`: 4
- `per_device_eval_batch_size`: 16
- `multi_dataset_batch_sampler`: round_robin

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `per_device_train_batch_size`: 16
- `num_train_epochs`: 4
- `max_steps`: -1
- `learning_rate`: 5e-05
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: None
- `warmup_steps`: 0
- `optim`: adamw_torch_fused
- `optim_args`: None
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `optim_target_modules`: None
- `gradient_accumulation_steps`: 1
- `average_tokens_across_devices`: True
- `max_grad_norm`: 1
- `label_smoothing_factor`: 0.0
- `bf16`: False
- `fp16`: False
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `use_liger_kernel`: False
- `liger_kernel_config`: None
- `use_cache`: False
- `neftune_noise_alpha`: None
- `torch_empty_cache_steps`: None
- `auto_find_batch_size`: False
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `include_num_input_tokens_seen`: no
- `log_level`: passive
- `log_level_replica`: warning
- `disable_tqdm`: False
- `project`: huggingface
- `trackio_space_id`: None
- `trackio_bucket_id`: None
- `trackio_static_space_id`: None
- `per_device_eval_batch_size`: 16
- `prediction_loss_only`: True
- `eval_on_start`: False
- `eval_do_concat_batches`: True
- `eval_use_gather_object`: False
- `eval_accumulation_steps`: None
- `include_for_metrics`: []
- `batch_eval_metrics`: False
- `save_only_model`: False
- `save_on_each_node`: False
- `enable_jit_checkpoint`: False
- `push_to_hub`: False
- `hub_private_repo`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_always_push`: False
- `hub_revision`: None
- `load_best_model_at_end`: False
- `ignore_data_skip`: False
- `restore_callback_states_from_checkpoint`: False
- `full_determinism`: False
- `seed`: 42
- `data_seed`: None
- `use_cpu`: False
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `parallelism_config`: None
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `dataloader_prefetch_factor`: None
- `remove_unused_columns`: True
- `label_names`: None
- `train_sampling_strategy`: random
- `length_column_name`: length
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `ddp_static_graph`: None
- `ddp_backend`: None
- `ddp_timeout`: 1800
- `fsdp`: []
- `fsdp_config`: {'min_num_params': 0, 'xla': False, 'xla_fsdp_v2': False, 'xla_fsdp_grad_ckpt': False}
- `deepspeed`: None
- `debug`: []
- `skip_memory_metrics`: True
- `do_predict`: False
- `resume_from_checkpoint`: None
- `warmup_ratio`: None
- `local_rank`: -1
- `prompts`: None
- `batch_sampler`: batch_sampler
- `multi_dataset_batch_sampler`: round_robin
- `router_mapping`: {}
- `learning_rate_mapping`: {}

</details>

### Training Logs
| Epoch | Step | Training Loss |
|:-----:|:----:|:-------------:|
| 1.0   | 500  | 0.0178        |
| 2.0   | 1000 | 0.0001        |
| 3.0   | 1500 | 0.0001        |
| 4.0   | 2000 | 0.0001        |


### Training Time
- **Training**: 5.5 hours

### Framework Versions
- Python: 3.13.3
- Sentence Transformers: 5.6.0
- Transformers: 5.6.2
- PyTorch: 2.11.0+cpu
- Accelerate: 1.13.0
- Datasets: 4.8.5
- Tokenizers: 0.22.2

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->