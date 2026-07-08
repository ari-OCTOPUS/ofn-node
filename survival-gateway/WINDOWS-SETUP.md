# راه‌اندازی روی Windows — بدونِ make (راه ب)

`make` لازم نیست؛ فقط **Docker Desktop**. این بسته از قبل GLM + DeepSeek + Fugu را سیم‌کشی شده دارد.

## گام ۰ — Docker Desktop
Start Menu → «Docker Desktop». اگر نیست، از docker.com نصب کن (با WSL2). روشنش کن تا آیکونش سبز شود.

## گام ۱ — این فولدر را بیرونِ vault بگذار
کلِ محتوای این بسته را در `F:\survival-gateway\` بگذار (نه در F:\backup).

## گام ۲ — .env بساز و کلیدها را پر کن (فقط این‌جا، هرگز git/چت)
```powershell
cd F:\survival-gateway
copy .env.example .env
notepad .env
```
در `.env` پر کن:
- `LITELLM_MASTER_KEY` و `LITELLM_SALT_KEY` و `POSTGRES_PASSWORD` (هر رشتهٔ تصادفیِ بلند)
- `DEEPSEEK_API_KEY` (از platform.deepseek.com)
- `ZAI_API_KEY` (از GLM Coding Plan)
- `SAKANA_API_KEY` (از console.sakana.ai)

## گام ۳ — بالا آوردن (به‌جای make up)
```powershell
docker compose up -d
docker compose ps
```

## گام ۴ — سلامت + تستِ سه route
```powershell
curl http://127.0.0.1:4000/health/liveliness
# GLM:
curl -s http://127.0.0.1:4000/v1/chat/completions -H "Authorization: Bearer <MASTER_KEY>" -H "Content-Type: application/json" -d "{\"model\":\"glm-coder\",\"messages\":[{\"role\":\"user\",\"content\":\"test\"}]}"
# DeepSeek:  model = deepseek-bulk
# Fugu:      model = orchestr
```

## کشتن (به‌جای make kill)
```powershell
docker compose down
```

## ⚠️ VERIFY قبل از اتکا (حدس نزن)
- GLM: model-id و api_base در `docs.z.ai`.
- Fugu: base_url در `console.sakana.ai` (عمومی نیست).
- DeepSeek: `deepseek/deepseek-v4-flash` — OK.
اگر یک route خطا داد، همان یکی را در `litellm_config.yaml` اصلاح کن؛ بقیه مستقل کار می‌کنند.
