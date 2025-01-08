const phoneInput = document.getElementById("phone");
const smsForm = document.getElementById("sms-form");
const loginForm = document.getElementById("login-content");
const errorMessage = document.getElementById("error-message"); // Telefon raqami xato xabari
const smsErrorMessage = document.getElementById("sms-error-message"); // SMS xato xabari
const loginSection = document.querySelector("#login-section");
const loginSmsContent = document.querySelector(".login-sms-content");
const loginContent = document.querySelector(".login-content");
const phonenumbersee = document.querySelector(".phonenumbersee");
const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');


// Telefon raqamini formatlash va o'zbekiston raqamiga mosligini tekshirish
phoneInput.addEventListener("input", function (e) {
    let input = e.target.value.replace(/\D/g, ""); // Faqat raqamlarni olib qolamiz

    // +998 ni saqlab qolish
    if (input.startsWith("998")) {
        input = input.substring(3); // 998 ni olib tashlaymiz
    }

    // Formatlash
    let formattedNumber = "+998";
    if (input.length > 0) {
        formattedNumber += " (" + input.substring(0, 2); // 90-99 kodlar uchun
    }
    if (input.length >= 3) {
        formattedNumber += ") " + input.substring(2, 5);
    }
    if (input.length >= 6) {
        formattedNumber += "-" + input.substring(5, 7);
    }
    if (input.length >= 8) {
        formattedNumber += "-" + input.substring(7, 9);
    }

    // Inputni yangilash
    e.target.value = formattedNumber;
});
if (window.location.hash === "#login"){
    LoginShow()
}


// Telefon raqami formatining to'g'riligini tekshirish
function validatePhoneNumber() {
    const phoneValue = phoneInput.value.replace(/\D/g, ""); // Faqat raqamlarni olib kelamiz

    // Raqamga mos bo'lmasa, xatolikni ko'rsatish
    if (phoneValue.length !== 12) {
        errorMessage.style.display = "block";
        errorMessage.textContent = "Iltimos, to'g'ri telefon raqamini kiriting!";
        return false;
    }
    return true;
}
function submitForm(phoneNumber) {
    const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    fetch('/account/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken // JSON formatida yuborish
        },
        body: JSON.stringify({ phone_number: phoneNumber }) // JSON formatida yuboriladigan ma'lumot
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json(); // Javobni JSON formatida o'qish
    })
    .then(data => {
        userId = data.user_id;
        form = document.querySelector('#sms-form')
        form.setAttribute("action", `/account/verify/${userId}/`)  
    })
    .catch((error) => {
        console.error('Error:', error); // Xatolik yuzaga keldi
    });
}
phoneInput.addEventListener("keydown", function (e) {
    // Agar foydalanuvchi +998 qismini o'chirishga harakat qilsa, to'xtatish
    if (e.key === "Backspace" && phoneInput.value.length <= 5) {
        e.preventDefault();
    }
});

// SMS kiritishni ko'rsatish
function LoginSmsShow(event) {
    event.preventDefault(); // Formani yuborishni to'xtatadi
    phonenumbersee.innerHTML = phoneInput.value;
    if (validatePhoneNumber()) {
        loginForm.classList.add("tag-hide"); // Telefon raqam kiritish formasi yashirinadi
        loginSmsContent.classList.remove("tag-hide"); // SMS formasi ko'rsatiladi
        errorMessage.style.display = "none"; // Telefon raqami to'g'ri bo'lsa, xato xabarini yashiradi
        submitForm(phoneInput.value.replace(/\D/g, ""))
    }
}

// Telefon raqamini tekshirish va formani yuborish

// SMS kodini tekshirish
smsForm.addEventListener("submit", function (e) {
    e.preventDefault(); // Formani yuborishni to'xtatadi
    const smsCode = document.getElementById("sms-code").value.trim();

    // SMS kodi 6 ta raqam bo'lsa, formani yuborish
    if (smsCode.length === 6 && /^[0-9]{6}$/.test(smsCode)) {
        smsErrorMessage.style.display = "none"; // Xato xabarini yashirish
        // Formani yuborish
        form = document.querySelector('#sms-form')
        const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        fetch(form.getAttribute("action"), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded', // yoki 'application/json' agar JSON yuborayotgan bo'lsangiz
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ verification_code: smsCode }) // JSON formatida yuboriladigan ma'lumot

    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.text(); // Yana HTML yoki JSON bo'lishi mumkin
    })
    .then(data => {
        console.log(document.querySelector('.next_value').value) // Javobni ko'
        if (data == "Tasdiqlash muvaffaqiyatli amalga oshirildi!") {
            // message
            if(document.querySelector('.next_value').value){
                window.location.href = document.querySelector('.next_value').value;
            }
            else{
                window.location.href = "/account/profile";
            }
        } else {
            // message
        }
    })
    .catch((error) => {
        console.error('Xatolik:', error);
    });

    } else {
        // SMS kodi noto'g'ri, xato xabarini ko'rsatish
        smsErrorMessage.style.display = "block";
        smsErrorMessage.textContent = "Iltimos, 6 xonali SMS kodni to'liq kiriting!";
    }
});

// Timer va qayta jo'natish funksiyasi
const sendButton = document.getElementById('sendButton');
const timerElement = document.getElementById('timer');
const codeInput = document.getElementById('code');
const errorMessage1 = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');

let countdown = 60; // 60 soniya
let correctCode = "123456"; // To'g'ri kod (namuna sifatida)
let timer; // Timerni ushlab turish uchun o'zgaruvchi

// Timerni ishga tushirish
function startTimer() {
    countdown = 60; // Har safar qayta boshlash uchun 60 ga qaytarish
    timerElement.innerText = `Agar kod kelmasa, siz ${countdown} soniya orqali yangisini olishingiz mumkin`;

    // Timer ishlashini ta'minlash
    timer = setInterval(() => {
        countdown--;
        timerElement.innerText = `Agar kod kelmasa, siz ${countdown} soniya orqali yangisini olishingiz mumkin`;

        if (countdown <= 0) {
            clearInterval(timer);
            timerElement.innerText = '';
            switchToResendButton(); // Tugmani "Qayta jo'natish" ga o'zgartirish
        }
    }, 1000);
}

// Jo'natish tugmasini "Qayta jo'natish" ga o'zgartirish
function switchToResendButton() {
    sendButton.innerText = "Qayta jo'natish"; // Tugma matni o'zgaradi
    sendButton.type = 'button';
    sendButton.classList.add('disabled');
    sendButton.removeEventListener('click', checkCode);
    sendButton.addEventListener('click', resendCode);
}

// Kodni tekshirish funksiyasi
function checkCode() {
    const enteredCode = codeInput.value;
    if (enteredCode === correctCode) {
        errorMessage1.style.display = 'none'; // Xato xabar yashiriladi
        successMessage.style.display = 'block'; // To'g'ri xabar ko'rsatiladi
    } else {
        successMessage.style.display = 'none'; // To'g'ri xabar yashiriladi
        errorMessage1.style.display = 'block'; // Xato xabar ko'rsatiladi
    }
}

// Qayta kod jo'natish funksiyasi
function resendCode() {
    // Kod qayta jo'natilganda xabarni interfeysda ko'rsatish
    submitForm(document.querySelector(".phonenumbersee").innerText.replace(/\D/g, ""))

    successMessage.style.display = 'none';
    errorMessage1.style.display = 'none';
    sendButton.innerText = "Jo'natish";
    sendButton.type = 'submit';
    sendButton.classList.remove('disabled');
    sendButton.removeEventListener('click', resendCode);
    sendButton.addEventListener('click', checkCode);
    startTimer(); // Timer qayta boshlanadi
}

// Jo'natish tugmasiga bosilganda
sendButton.addEventListener('click', checkCode);

// Boshlanishida timerni ishga tushirish
startTimer();



// Loginni ko'rsatish yoki yashirish
function LoginShow() {
    loginSection.classList.toggle("login-show");
    loginSmsContent.classList.add("tag-hide");
    loginContent.classList.remove("tag-hide");
}











function toggleWishlist(element) {
    $(element).toggleClass('select');
  }







































function descShow() {
  document.querySelector("#description").classList.toggle("active")

}




















function SeeAllProduct(){
    document.querySelector(".seeallproduct").classList.toggle("seeallproduct-dn")
}


// review 

function rateProduct(productId, ratingValue) {
    fetch("/rate-product/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken
        },
        body: JSON.stringify({
            product_id: productId,
            rating: ratingValue
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage("Reyting muvaffaqiyatli qo'shildi yoki yangilandi!");
        } else {
            showMessage("Xato: " + data.error);
        }
    })
    .catch(error => {
        console.error("Xatolik:", error);
    });
}


// LIKE SCRIPTS

function toggleFavorite(productId) {
    fetch(`/toggle-favorite/${productId}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrftoken,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'added') {
            showMessage("Mahsulot sevimlilarga qo'shildi!");
        } else if (data.status === 'removed') {
            showMessage("Mahsulot sevimlilardan olib tashlandi!");
        } else {
            showMessage("Xato sodir bo'ldi.");
        }
    })
    .catch(error => {
        console.error("Xatolik:", error);
    });
}


// CART SCRIPTS

function addToCart(productId) {
    // Fetch so'rovini yuborish
    let quantity = document.getElementById('numberInput') ? document.getElementById('numberInput').value : 1;
    let colorId = document.getElementById('selectedColorId').value;
    if(!colorId){
        showMessage("Mahsulotni rangini tanlang")
        return "nimadur"
    }
    console.log(`${quantity}  -- ${colorId}`)
    fetch("/cart/add-to-cart/", {
        method: "POST",  // POST so'rovi
        headers: {
            "Content-Type": "application/json",  // JSON formatida so'rov yuborish
            "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({
            product_id: productId,  // Mahsulot ID
            color_id: parseInt(colorId),      // Rang ID
            quantity: quantity      // Mahsulot miqdori
        })
    })
    .then(response => response.json())  // JSON formatida javob olish
    .then(data => {
        // Javobni tekshirish va yangilash
        if (data.message) {
            showMessage(data.message); // Mahsulot qo'shilganligi haqida bildirishnoma
            
            // Savatdagi mahsulotlar sonini yangilash
            let cartCountElements = document.getElementsByClassName("cart-count");
            for (let element of cartCountElements) {
                element.innerText = data.cart_count; // Har bir elementni yangilash
            }
            document.querySelector('.cart_total_price').innerText = data.cart_total_price
        }
    })
    .catch(error => {
        console.error("Error:", error); // Agar xatolik bo'lsa, uni konsolga chiqarish
    });
}


function addToCartHome(button) {
    productId = button.getAttribute('data-product-id')
    quantity = 1
    quantity = quantity && quantity.value ? parseInt(quantity.value) : 1;
    const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    fetch('/cart/add-to-cart/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken// CSRF token olish
        },
        body: JSON.stringify({
          "product_id": productId,
          "quantity": quantity,
          "color_id":document.querySelector('.myCheckbox'+productId).value,
        })
    })
    .then(response => {
      if (!response.ok) {
          throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
        showMessage(data.message)
        let cartCountElements = document.getElementsByClassName("cart-count");
        for (let element of cartCountElements) {
            element.innerText = data.cart_count; // Har bir elementni yangilash
        }
        document.querySelector('.cart_total_price').innerText = data.cart_total_price
    })
    .catch(error => console.error('Error:', error));
}



// message
function showMessage(text){
    const cartAlert = document.getElementById('cart-alert');
	cartAlert.style.display = 'block';
    cartAlert.textContent = text;
    setTimeout(function () {
        cartAlert.style.display = 'none';
      }, 3000);
}
