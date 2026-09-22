#!/usr/bin/env bash
#
# Viet lai toan bo lich su git de:
#   1. Bo dong "Co-Authored-By: Claude ..." khoi 51 commit message
#   2. Go han docs/DeTai10.pdf ra khoi 100 commit  -- file hop dong co so CCCD,
#      so tai khoan ngan hang, ma so sinh vien va email ca nhan; repo PUBLIC
#
# Ban goc cua file do da duoc chuyen ra
#   D:/Documents/Project/NCKH_Document/DeTai10_hopdong_10TN-2026.pdf
# va doi chieu sha256 khop voi ban trong git truoc khi go.
#
# CHAY:  bash scripts/viet_lai_lich_su.sh
#
# ============================ DOC TRUOC KHI CHAY ============================
#
# Lenh nay doi TOAN BO commit hash. Hau qua:
#
#  - Ai da clone repo nay phai clone lai; `git pull` se bao phan ky.
#  - Hash 19beb18 ma bai bao dang trich trong sections/04_setup.tex se khong
#    con ton tai. Sau khi chay xong phai cap nhat no (buoc 8 o duoi).
#  - Tam 8 nhanh cu tren GitHub se bi xoa. Da kiem: ca 8 deu merge het vao
#    master, khong nhanh nao con commit rieng.
#
# Lenh KHONG lam duoc:
#  - Khong go duoc file khoi ban sao ma nguoi khac da clone.
#  - Khong go duoc khoi cache cua GitHub ngay lap tuc; muon chac thi sau khi
#    day xong, mo mot issue yeu cau GitHub Support xoa cache cua cac commit cu.
#
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

# Thu muc sao luu. Duong dan kieu Windows "D:/..." chi dung duoc trong Git Bash;
# chay bang WSL thi no bi hieu la duong dan TUONG DOI va bundle se do vao
# /mnt/d/QSVM_NSLKDD/D:/... -- dung loi da lam script chet lan dau.
if [ -d /mnt/d ]; then
    BACKUP_DIR="/mnt/d/Documents/Project/NCKH_Document"     # WSL
else
    BACKUP_DIR="D:/Documents/Project/NCKH_Document"          # Git Bash
fi
[ -d "$BACKUP_DIR" ] || { echo "LOI: khong thay thu muc sao luu $BACKUP_DIR"; exit 1; }

echo "== 1. Kiem tra dieu kien =="
[ -z "$(git status --porcelain)" ] || { echo "LOI: cay lam viec chua sach. Commit hoac stash truoc."; exit 1; }
[ "$(git rev-parse --abbrev-ref HEAD)" = "master" ] || { echo "LOI: phai dang o master."; exit 1; }
git fetch --prune
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/master)" ] || { echo "LOI: master local va origin/master khac nhau."; exit 1; }
echo "   OK"

echo
echo "== 2. Sao luu =="
STAMP=$(date +%Y%m%d_%H%M)
git bundle create "$BACKUP_DIR/QSVM_NSLKDD_backup_$STAMP.bundle" --all
git bundle verify "$BACKUP_DIR/QSVM_NSLKDD_backup_$STAMP.bundle" | tail -2
git tag -f "truoc-khi-viet-lai-$STAMP"
echo "   Sao luu: $BACKUP_DIR/QSVM_NSLKDD_backup_$STAMP.bundle"
echo "   Muon quay ve:  git clone <duong-dan-bundle> QSVM_NSLKDD_phuc_hoi"

echo
echo "== 3. Dem truoc khi sua =="
echo "   commit co dong Co-Authored-By: Claude : $(git log --all --format='%H' | while read -r h; do git log -1 --format='%B' "$h" | grep -q '^Co-Authored-By: Claude' && echo x || true; done | wc -l)"
echo "   commit con chua docs/DeTai10.pdf      : $(git rev-list --all | while read -r h; do git cat-file -e "$h:docs/DeTai10.pdf" 2>/dev/null && echo x || true; done | wc -l)"

echo
echo "== 4. Xoa 8 nhanh cu tren GitHub (deu da merge vao master) =="
for b in C2_noise_10run chore/tach-thu-muc-cu-moi docs/code-bo-sung \
         docs/doi-chieu-cu-moi docs/sap-xep-va-danh-dau \
         fix/audit-provenance-after-clone fix/untrack-c3-kernel-cache revisionC4; do
    git push origin --delete "$b" 2>/dev/null && echo "   xoa $b" || echo "   (khong co $b)"
done
# Nhanh local tuong ung, de --all khong keo lich su cu quay lai
for b in chore/tach-thu-muc-cu-moi docs/code-bo-sung docs/doi-chieu-cu-moi \
         docs/sap-xep-va-danh-dau fix/audit-provenance-after-clone \
         fix/untrack-c3-kernel-cache refactor/restructure-qsvm-pipeline revisionC4; do
    git branch -D "$b" 2>/dev/null || true
done
git fetch --prune
# Xoa cac tag moc an toan truoc khi loc: --tag-name-filter se viet lai chung
# thanh tro vao lich su MOI, nen mot tag ten "truoc khi viet lai" lai tro vao
# sau khi viet lai -- gay hieu nham. Ban bundle o buoc 2 da giu vai tro do.
git tag -l 'truoc-khi-viet-lai*' | while read -r t; do git tag -d "$t"; done

echo
echo "== 5. Viet lai lich su =="
# Ba viec, khong phai hai:
#  1. Bo trailer Co-Authored-By: Claude
#  2. Go CA HAI file nhay cam. Commit 886e78a goi chung la "hai file KHONG
#     duoc nam tren repo cong khai"; truoc day script chi go mot.
#  3. Sua thong diep cua chinh commit 886e78a. Go file ma de nguyen cau do
#     thi van con BIEN CHI DUONG: nguoi ngoai doc thay "co hai file khong
#     duoc cong khai o day" roi di tim. Ca hai ban sao luu da doi chieu
#     sha256 khop voi ban trong git truoc khi go.
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f \
    --msg-filter 'sed -e "/^Co-Authored-By: Claude/d" \
                      -e "s/go hai file KHONG duoc nam tren repo cong khai/sap xep lai thu muc tai lieu/"' \
    --index-filter 'git rm --cached --ignore-unmatch -q \
                      docs/DeTai10.pdf docs/PAPER1_final_report.docx' \
    --tag-name-filter cat -- --all

echo
echo "== 6. Doi chieu sau khi sua =="
LEFT_MSG=$(git log --all --format='%H' | while read -r h; do git log -1 --format='%B' "$h" | grep -q '^Co-Authored-By: Claude' && echo x || true; done | wc -l)
LEFT_PDF=$(git rev-list --all | while read -r h; do git cat-file -e "$h:docs/DeTai10.pdf" 2>/dev/null && echo x || true; done | wc -l)
LEFT_DOC=$(git rev-list --all | while read -r h; do git cat-file -e "$h:docs/PAPER1_final_report.docx" 2>/dev/null && echo x || true; done | wc -l)
LEFT_SIGN=$(git log --all --format='%s' | grep -c 'KHONG duoc nam tren repo cong khai' || true)
echo "   con dong Co-Authored-By: Claude : $LEFT_MSG    (phai la 0)"
echo "   con docs/DeTai10.pdf            : $LEFT_PDF    (phai la 0)"
echo "   con docs/PAPER1_final_report.docx: $LEFT_DOC   (phai la 0)"
echo "   con bien chi duong trong msg    : $LEFT_SIGN    (phai la 0)"
[ "$LEFT_MSG" -eq 0 ] && [ "$LEFT_PDF" -eq 0 ] \
    && [ "$LEFT_DOC" -eq 0 ] && [ "$LEFT_SIGN" -eq 0 ] \
    || { echo "LOI: van con sot. KHONG day len."; exit 1; }
echo "   so commit: $(git log --oneline | wc -l)  (truoc khi sua: xem buoc 3)"

echo
echo "== 7. Don rac va day len =="
rm -rf .git/refs/original
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo "   Sap day len GitHub. Day la buoc KHONG quay lai duoc bang git."
read -r -p "   Go 'DONG Y' roi Enter de day: " ans
[ "$ans" = "DONG Y" ] || { echo "   Da dung, chua day gi len."; exit 0; }
git push --force --all
# Khong day tag len: repo khong co tag that nao, cac tag moc an toan da xoa
# o buoc 4, va ban sao luu la file bundle chu khong phai tag.

echo
echo "== 8. Con phai lam bang tay =="
echo "   a. Cap nhat commit hash trong paper/paper1/sections/04_setup.tex:"
echo "      hash cu 19beb18 khong con ton tai. Hash moi cua HEAD:"
echo "      $(git rev-parse --short HEAD)"
echo "      (nen cap nhat lai lan nua ngay truoc khi nop)"
echo "   b. Bao Quang Anh va cac thanh vien khac clone lai repo."
echo "   c. Neu muon chac GitHub khong con cache commit cu: mo issue voi"
echo "      GitHub Support, keo theo danh sach hash cu."
echo
echo "Xong."
