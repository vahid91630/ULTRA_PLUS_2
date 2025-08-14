async function fetchStatus(){
  try{
    const r = await fetch('/api/status', {cache:'no-store'});
    const data = await r.json();

    const exId = document.getElementById('ex-id');
    const exAuth = document.getElementById('ex-auth');
    const exErr = document.getElementById('ex-error');
    if(data.exchange_status && data.exchange_status.ok){
      exId.textContent = `MEXC ✓`;
      if (data.exchange_status.auth === true){
        exAuth.textContent = 'احراز موفق (کلیدها درست‌اند)';
        exAuth.className = 'badge ok';
      } else if (data.exchange_status.auth === false){
        exAuth.textContent = 'احراز ناموفق (کلید/مجوز مشکل دارد)';
        exAuth.className = 'badge bad';
      } else {
        exAuth.textContent = 'بدون کلید (مشاهده بازار فقط)';
        exAuth.className = 'badge';
      }
      exErr.textContent = data.exchange_status.error ? `خطا: ${data.exchange_status.error}` : '';
    } else {
      exId.textContent = 'MEXC ✗';
      exAuth.textContent = 'اتصال مشکل دارد';
      exAuth.className = 'badge bad';
      exErr.textContent = data.exchange_status ? (data.exchange_status.error || '') : 'نامشخص';
    }

    const mgDb = document.getElementById('mg-db');
    const mgCols = document.getElementById('mg-cols');
    const mgErr = document.getElementById('mg-error');
    if(data.mongo && data.mongo.ok){
      mgDb.textContent = `اتصال به: ${data.mongo.db}`;
      mgCols.textContent = `کالکشن‌ها: ${Array.isArray(data.mongo.collections)? data.mongo.collections.join(', ') : '—'}`;
      mgErr.textContent = '';
    } else {
      mgDb.textContent = 'بدون اتصال';
      mgCols.textContent = '';
      mgErr.textContent = data.mongo ? (data.mongo.error || '') : 'MONGO_URL تعریف نشده است';
    }

    const sb = document.getElementById('cfg-sandbox');
    sb.textContent = data.sandbox === 'true' ? 'فعال' : 'خاموش';

    document.getElementById('log-box').textContent = JSON.stringify(data, null, 2);
  }catch(e){
    document.getElementById('log-box').textContent = 'خطا در دریافت وضعیت: ' + e;
  }
}
fetchStatus();
setInterval(fetchStatus, 8000);
