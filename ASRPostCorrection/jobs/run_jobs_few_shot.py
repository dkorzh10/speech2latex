
import os
import sys

from mls.manager.job.utils import training_job_api_from_profile

if __name__ == "__main__":

    dry_run = len(sys.argv) > 1 and sys.argv[1] == 'dry'

    client, extra_options = training_job_api_from_profile('default')

    workdir = os.getcwd()

    env_prefix = '/workspace-SR004.nfs2/d.tarasov/envs/dtarasov-speech2latex/bin'

    author_name = 'd.tarasov'

    models = [ 'Qwen/Qwen2.5-0.5B-Instruct', 'Qwen/Qwen2.5-1.5B-Instruct', 'Qwen/Qwen2.5-Math-1.5B-Instruct', 'Qwen/Qwen2.5-7B-Instruct' ]

    for model in models:
        for data_type in ['human', 'synthetic_small', 'mix']:

            for n_few_shot in [ 25 ]:
            # for n_few_shot in [5, 25]:

                command = f"cd {workdir} && {env_prefix}/python sentences-few-shot.py --model {model} --data_type {data_type} --n_few_shot {n_few_shot}"
                print("\n\n", command)
                if dry_run:
                    continue

                result = client.run_job(
                    payload={
                        'script': command,
                        'job_desc': f'S2L: Few Shot {model} {data_type} n_few_shot={n_few_shot} #{author_name} #rnd #multimodal  #notify_completed @mrsndmn',
                        'env_variables': {
                            'PYTHONPATH': './:../src:/workspace-SR004.nfs2/d.tarasov/ProcessLaTeXFormulaTools/:../TeXBLEU',
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

                print("model", model, "data_type", data_type, "n_few_shot", n_few_shot, "result", result)

