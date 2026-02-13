
rm -rf ./supplemetnary/ supplemetnary.zip
mkdir -p ./supplemetnary/source_code/

cp -r .git ./supplemetnary/source_code/.git

cd ./supplemetnary/source_code/

# Восстанавливаем только закоммиченные файлы
git checkout .

# Удаляем все файлы, которые могут задеанонить (джобы, гит, скрипты c полными путями)
# Скрипты джобов для воспроизводимости не нужны и из них нельзя просто выкинуть полные пути (хотя можно, но костыльно это будет и неудобно)
rm -rf .git/ prepare_submission.sh

echo "Following files will be deleted:"
grep -Rl tarasov .
# echo "Press Enter to continue"
# read -n 1 -s


grep -Rl tarasov . | xargs rm

rm -rf ASRDataCreator ASR_FT RusTTS EngTTS Data/latex_in_context/README.md Data/latex_in_context_tts/latex_in_context_15k_filtered_with_transcriptions.jsonl Data/our_datasets requirements.txt

find -name .ipynb_checkpoints -type d -exec rm -rf {} +

if ! grep --binary-files=without-match -PRi 'sber|Nikita|korzh|iudin|karimov|elvir|tarasov|mrsndmn|\brsi\b|[а-яА-ЯёЁ]' . |  grep -v 'TeXBLEU/tokenizer.json\|TeXBLEU/new_embeddings.pth\|.csv' |  grep -q .; then
    echo "✅ No matching deanon substrings found."
else
    grep --binary-files=without-match -PRi 'sber|Nikita|korzh|iudin|karimov|elvir|tarasov|mrsndmn|\brsi\b|[а-яА-ЯёЁ]' . |  grep -v 'TeXBLEU/tokenizer.json\|TeXBLEU/new_embeddings.pth\|.csv' | head
    echo "❌ Matching deanon substrings found!"
    exit 1
fi

if ! find . -type f -regex '.*/\(sber\|Nikita\|korzh\|iudin\|karimov\|elvir\|mrsndmn\|tarasov\|rsi\).*' | grep -q .; then
    echo "✅ No matching deanon files found."
else
    echo "❌ Matching deanon files found!"
    exit 1
fi


echo "Sample datasets data"
python sample_datasets.py

if [ $? -ne 0 ]; then
    echo "❌ Sample datasets data creation failed!"
    exit 1
fi

rm sample_datasets.py

mv ./sample_datasets ../
# mv ./Speech2Latex_APPENDIX.pdf ../

cd ../../


# Create new archive
rm -rf supplemetnary.zip
zip -r supplemetnary.zip ./supplemetnary/

# Assert result archive size less 50MB
FILE_SIZE=$(stat -c%s "supplemetnary.zip")  # GNU stat (Linux)

MAX_SIZE=$((45 * 1024 * 1024))  # 45MB in bytes

if [ "$FILE_SIZE" -lt "$MAX_SIZE" ]; then
    echo "✅ Archive size is less than 50MB."
else
    echo "❌ Archive size is greater than or equal to 50MB."
    du -sh supplemetnary.zip
    exit 1  # or handle the error as needed
fi
