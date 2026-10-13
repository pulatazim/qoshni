# 1. Modulli monolit

Status: qabul qilingan (2026-10-13)

Yolg'iz dasturchi, kuniga 2-3 soat. Mikrosvrislar o'rniga bitta FastAPI ilovasi va bitta
ARQ worker'i: bitta bazadan tranzaksiya, bitta deploy, bitta log oqimi. Kod modullarga
bo'lingan (`app/modules/*`), har bir modul o'z router/service/schema'siga ega, shuning
uchun biror modulni alohida servisga chiqarish kerak bo'lsa, chegara allaqachon toza.

Narxi: parallel deploy va mustaqil masshtablash yo'q. 10 000 faol foydalanuvchigacha bu
narx to'lanmaydi; ochilganda chat yoki bildirishnoma moduli birinchi ajraladi.
