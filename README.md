# 名古屋看花花

11/17–11/24 名古屋 8 天行程的手機網頁 App：行程、天氣、交通、記帳與清單。

- 網址：https://timern0803.github.io/nagoya-trip/
- 加到主畫面後會全螢幕開啟，行程與交通離線也能看。
- 記帳與清單透過 Firebase 兩人同步，需要輸入旅行代碼。

## Firestore 安全規則

只有知道旅行代碼的人能讀寫，代碼不寫在程式碼裡。

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /trips/{trip}/{document=**} {
      allow read, write: if trip == "旅行代碼";
    }
  }
}
```
