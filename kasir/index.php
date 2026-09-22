<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ada pesan buat kamu ❤️</title>
    <style>
        body {
            font-family: 'Poppins', sans-serif;
            background-color: #ffe6e6;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }
        .container {
            text-align: center;
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            max-width: 400px;
            width: 90%;
            position: relative;
            z-index: 2;
        }
        h1 {
            color: #ff4d6d;
            font-size: 24px;
            margin-bottom: 20px;
        }
        p {
            color: #4f5d75;
            font-size: 16px;
            line-height: 1.6;
        }
        .emoji {
            font-size: 50px;
            margin-bottom: 10px;
            animation: pulse 1.5s infinite;
        }
        .btn-group {
            margin-top: 30px;
            display: flex;
            justify-content: center;
            gap: 20px;
        }
        button {
            padding: 12px 30px;
            font-size: 16px;
            font-weight: bold;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        #btn-yes {
            background-color: #ff4d6d;
            color: white;
        }
        #btn-yes:hover {
            transform: scale(1.1);
        }
        #btn-no {
            background-color: #6c757d;
            color: white;
            position: absolute;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
    </style>
</head>
<body>

    <div class="container" id="main-card">
        <div class="emoji" id="emoji-box">✨</div>
        <h1 id="headline">Hai Kamu... 😊</h1>
        <p id="message">Aku udah lama mendam perasaan ini. Lewat codingan sederhana ini, aku cuma mau jujur... Kamu mau gak jadi pacarku? ❤️</p>
        
        <div class="btn-group" id="buttons">
            <button id="btn-yes" onclick="terimaCinta()">Mau</button>
            <button id="btn-no" onmouseover="lari()" onclick="lari()">Gak Mau</button>
        </div>
    </div>

    <script>
        const btnNo = document.getElementById('btn-no');
        const headline = document.getElementById('headline');
        const message = document.getElementById('message');
        const emojiBox = document.getElementById('emoji-box');
        const btnYes = document.getElementById('btn-yes');

        // Fungsi membuat tombol "Gak Mau" lari menjauh
        function lari() {
            const width = window.innerWidth - btnNo.offsetWidth - 20;
            const height = window.innerHeight - btnNo.offsetHeight - 20;
            
            // Acak posisi baru tombol
            const randomX = Math.floor(Math.random() * width);
            const randomY = Math.floor(Math.random() * height);
            
            btnNo.style.left = randomX + 'px';
            btnNo.style.top = randomY + 'px';
        }

        // Fungsi ketika tombol "Mau" diklik
        function terimaCinta() {
            emojiBox.innerHTML = "💖";
            headline.innerHTML = "Yeeeey! I Love You! 🥰";
            message.innerHTML = "Makasih ya udah mau nerima aku! Janji deh gabakal bikin kamu nyesel. Kabari aku lewat WhatsApp sekarang ya! 😚🎉";
            
            // Sembunyikan tombol "Gak Mau" dan ubah tombol "Mau" menjadi link WA
            btnNo.style.display = 'none';
            btnYes.innerHTML = "Hubungi Aku 📱";
            btnYes.setAttribute("onclick", "kirimWA()");
        }

        // Otomatis kirim pesan konfirmasi ke WhatsApp Anda
        function kirimWA() {
            const nomorWA = "6285134345328"; // Ganti dengan nomor WhatsApp Anda
            const teks = encodeURIComponent("Iya, aku mau jadi pacar kamu! 🥰❤️");
            window.open(`https://api.whatsapp.com/send/?phone=+6285134345328&text&type=phone_number&app_absent=0&wame_ctl=1}&text=${teks}`, '_blank');
        }
    </script>

</body>
</html>
