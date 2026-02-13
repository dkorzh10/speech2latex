import glob
import os
import sys
from mls.manager.job.utils import training_job_api_from_profile

if __name__ == "__main__":

    dry_run = len(sys.argv) > 1 and sys.argv[1] == 'dry'

    client, extra_options = training_job_api_from_profile('default')

    workdir = os.getcwd()

    env_prefix = '/workspace-SR004.nfs2/d.tarasov/envs/dtarasov-speech2latex/bin'

    author_name = 'd.tarasov'

    config_name_all = glob.glob("configs/config_base*.json")
    # config_name_all = config_name_all[:1]
    config_name_all = [
        'configs/config_base_r8-a32-lr1e-4.json',
        # 'configs/config_base_r16-a32-lr1e-4.json',
        'configs/config_base_r16-a64-lr1e-4.json',
    ]

    for config_name in config_name_all:
        for dataset_split in ['equations']:
        # for dataset_split in ['sentences', 'equations']:
            # for latex_column_name in ['sentence', 'sentence_normalized']:
            # for latex_column_name in ['sentence_normalized']:
            for latex_column_name in ['sentence']:
                # for language in ['multilingual']:
                for language in ['eng']:
                # for language in ['eng', 'ru', 'multilingual']:
                    if dataset_split == 'sentences' and (language == 'ru' or language == 'multilingual'):
                        continue

                    # for data_type in ['mix_full']:
                    # for data_type in ['human', 'synthetic_small', 'mix']:
                    for data_type in ['mix']:

                        script = f"cd {workdir} && {env_prefix}/python train.py --config {config_name} --dataset_split {dataset_split} --latex_column_name {latex_column_name} --language {language} --data_type {data_type}"

                        print("\n\nscript", script)
                        if dry_run:
                            continue

                        result = client.run_job(
                            payload={
                                'script': script,
                                'job_desc': f'S2L: Qwen Audio FT {config_name} {dataset_split} lang={language} data={data_type} #{author_name} #rnd #multimodal @mrsndmn #notify_completed',
                                'env_variables': {
                                    'PYTHONPATH': '/workspace-SR004.nfs2/d.tarasov/speech2latex-gh:/workspace-SR004.nfs2/d.tarasov/ProcessLaTeXFormulaTools:./:../src:../TeXBLEU:../TeXBLEU:/workspace-SR004.nfs2/d.tarasov/speech2latex-gh/src:../TeXBLEU:/workspace-SR004.nfs2/d.tarasov/speech2latex-gh/src:/workspace-SR004.nfs2/d.tarasov/speech2latex-gh/TeXBLEU',
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

                        print("dataset_split", dataset_split, "latex_column_name", latex_column_name, "language", language, "data_type", data_type, "result", result)

