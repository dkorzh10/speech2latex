
import os

from mls.manager.job.utils import training_job_api_from_profile

if __name__ == "__main__":

    client, extra_options = training_job_api_from_profile('default')

    workdir = os.getcwd()

    # For test transcription run following command:
    # python ASR_s2l_equations.py --model_type base --dataset_path ../../Data/trainable_split/equations_test_new --output_prefix ../Experiments/result_ASR_s2l_equations_test_
    # python ASR_s2l_equations.py --model_type small --dataset_path ../../Data/trainable_split/equations_test_new --output_prefix ../Experiments/result_ASR_s2l_equations_test_

    author_name = 'd.tarasov'

    total_shards = 6
    # Train transcription
    for shard_number in range(total_shards):
        for model_type in [ 'base', 'small' ]:
            result = client.run_job(
                payload={
                    'script': f"bash {workdir}/run_jobs_asr_s2l_equations.sh --model_type {model_type} --shard_number {shard_number} --total_shards {total_shards}",
                    'job_desc': f'ASR S2L Equations {model_type} shard {shard_number} of {total_shards} #{author_name} #rnd #multimodal  #notify_completed @mrsndmn',
                    'env_variables': {
                        'PYTHONPATH': './',
                        'HF_HOME': '/workspace-SR004.nfs2/.cache/huggingface',
                    },
                    'instance_type': 'a100.1gpu',
                    'region': extra_options['region'],
                    'type': 'binary_exp',
                    'shm_size_class': 'medium',
                    'base_image': 'cr.ai.cloud.ru/aicloud-base-images/cuda12.1-torch2-py311:0.0.36',
                    'n_workers': 1,              # Количество воркеров.
                    'processes_per_worker': 1,   # Количество процессов на воркер. Для accelerate нужно запускать 1 процесс на воркер. Для torchrun лучше не заполнять этот параметр. По умолчанию запускается по количеству GPU на одном воркере - это подходит для torchrun.
                }
            )

            print(model_type, shard_number, result)

