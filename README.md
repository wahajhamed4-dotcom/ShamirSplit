# ShamirSplit

**ShamirSplit** أداة سطر أوامر ومكتبة Pure Python لتقسيم سر أو ملف إلى عدة مشاركات، ثم إعادة بنائه عند توفر حد أدنى منها. تعتمد الأداة على **Shamir's Secret Sharing** فوق الحقل المنتهي GF(256)، وتستخدم مولد العشوائية الآمن `secrets` المدمج في Python.

## الفكرة

يُقسَّم السر إلى `n` مشاركات، ويُحدد حد أدنى `k` بحيث لا يمكن إعادة البناء بأقل من `k` مشاركات. مثال: الإعداد `5/3` ينشئ خمس مشاركات، وتكفي أي ثلاث منها لإعادة السر. لا توجد تبعيات خارجية.

> هذه الأداة لا تشفّر المشاركة بحد ذاتها ولا تحمي ملفات المشاركة من الوصول غير المصرح به. احفظها بصلاحيات مناسبة، واستخدم قناة آمنة لنقلها.

## المتطلبات والتثبيت

- Python 3.10 أو أحدث.
- لا تحتاج إلى Third-party Libraries.

من مجلد المشروع:

```bash
python -m venv .venv
# Linux/macOS
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
```

ويمكن التشغيل مباشرة دون تثبيت:

```bash
python -m shamirsplit.cli --help
```

## الاستخدام

### تقسيم ملف

```bash
shamirsplit split secret.txt --shares 5 --threshold 3 --output-dir shares
```

أو:

```bash
python -m shamirsplit.cli split secret.txt -n 5 -t 3 -o shares
```

ينتج الأمر ملفات مثل `share-001.json` و`share-002.json`. تحتوي الملفات على بيانات المشاركة، رقمها، الحد الأدنى، إجمالي العدد، وبصمة SHA-256 للسر للتحقق بعد إعادة البناء.

### إعادة البناء

```bash
shamirsplit reconstruct shares/share-001.json shares/share-003.json shares/share-005.json -o restored.txt
```

لا تُكتب النتيجة إذا كانت المشاركة ناقصة أو غير متوافقة أو فشلت البصمة.

### ملف إعدادات

يمكن تمرير الإعدادات الافتراضية من JSON:

```bash
shamirsplit split secret.txt --config config.example.json
```

مثال الملف:

```json
{
  "shares": 5,
  "threshold": 3
}
```

خيارات عامة:

```text
--help       عرض المساعدة
--version    عرض الإصدار
--config     تحميل إعدادات JSON
--log-level  CRITICAL | ERROR | WARNING | INFO | DEBUG
```

## اختبار المشروع

```bash
python -m unittest discover -s tests -v
```

## بنية المشروع

| المسار | الوصف |
|---|---|
| `shamirsplit/core.py` | حسابات GF(256) وخوارزمية التقسيم وإعادة البناء |
| `shamirsplit/format.py` | تنسيق JSON وقراءة/كتابة ملفات المشاركات |
| `shamirsplit/cli.py` | واجهة سطر الأوامر ومعالجة الأخطاء |
| `tests/` | اختبارات الوحدة |
| `config.example.json` | إعدادات نموذجية |

## حدود التصميم

تدعم الخوارزمية من 2 إلى 255 مشاركة، ومن 2 إلى `n` كحد أدنى. تتم معالجة البيانات كخانات بايت، لذلك يمكن استخدامها مع النصوص والملفات الثنائية. مشاركة واحدة لا تكشف بايتات السر الأصلية عند استخدام حد أدنى أكبر من واحد، لكن أمان التشغيل يعتمد أيضاً على حماية ملفات المشاركة وسلامة بيئة التشغيل.

## الترخيص

مشروع تعليمي قابل للتطوير. راجع سياسة الترخيص التي سيضيفها فريق المشروع قبل النشر العام.
