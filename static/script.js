document.querySelectorAll('a[href^="#"]').forEach(link => {
  link.addEventListener('click', function(e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth' });
    }
  });
});
document.addEventListener("DOMContentLoaded", function() {
  const menuToggle = document.querySelector('.menu-toggle');
  const menu = document.querySelector('.menu');
  if (menuToggle && menu) {
    menuToggle.addEventListener('click', function() {
      menu.classList.toggle('show');
    });
    // Opcional: cerrar menú al hacer click en un enlace
    menu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => menu.classList.remove('show'));
    });
  }
});
// ======= SUBIR IMAGEN =======
function enviarImagen() {
  const archivo = document.getElementById("imagen").files[0];
  const preview = document.getElementById("preview");
  const resultadoImagen = document.getElementById("resultado-imagen");

  if (!archivo) {
    alert("Por favor selecciona una imagen.");
    return;
  }

  const reader = new FileReader();
  reader.onload = function (e) {
    preview.innerHTML = `<img src="${e.target.result}" alt="Imagen seleccionada" style="max-width: 300px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">`;
  };
  reader.readAsDataURL(archivo);

  const formData = new FormData();
  formData.append("file", archivo);
/* */
  fetch("https://tr4f1c0.onrender.com/predict/", {
    method: "POST",
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      resultadoImagen.textContent = `📌 Resultado: ${data.prediction}`;
    })
    .catch(err => {
      resultadoImagen.textContent = "❌ Error al realizar la predicción.";
      console.error(err);
    });
}

// ======= CÁMARA EN TIEMPO REAL =======
const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const resultadoCamara = document.getElementById("resultado-camara");
const ctx = canvas.getContext("2d");

let usandoFrontal = true;
let stream = null;
let ejecutando = true;

async function iniciarCamara() {
  ejecutando = true;

  if (stream) {
    stream.getTracks().forEach(track => track.stop());
  }

  try {
    const permisos = await navigator.permissions.query({ name: 'camera' });
    if (permisos.state === "denied") {
      resultadoCamara.textContent = "🚫 Permiso denegado para usar la cámara.";
      return;
    }
  } catch (e) {
    console.warn("El navegador no soporta permissions.query:", e);
  }

  const constraints = {
    video: {
      facingMode: usandoFrontal ? "user" : "environment"
    }
  };

  try {
    stream = await navigator.mediaDevices.getUserMedia(constraints);
    video.srcObject = stream;
    procesarFrame();
  } catch (err) {
    resultadoCamara.textContent = "❌ No se pudo acceder a la cámara.";
    console.error(err);
  }
}


function procesarFrame() {
  if (!ejecutando) return;

  if (video.readyState === video.HAVE_ENOUGH_DATA) {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(blob => {
      const formData = new FormData();
      formData.append("file", blob, "frame.jpg");

      fetch("https://tr4f1c0.onrender.com/predict/realtime/", {
        method: "POST",
        body: formData
      })
        .then(res => res.json())
        .then(data => {
          if (data.nombre) {
            resultadoCamara.innerHTML = `
              🛑 <strong>Señal detectada:</strong> ${data.nombre}
              📈 <strong>Confianza:</strong> ${data.confianza}%`;
          } else {
            resultadoCamara.textContent = "⚠️ Clase desconocida.";
          }
        })
        .catch(err => {
          resultadoCamara.textContent = "❌ Error en la predicción.";
          console.error(err);
        });
    }, "image/jpeg");
  }

  setTimeout(procesarFrame, 1500); // Cada 1.5 segundos
}

// Botón detener cámara
document.getElementById("btn-detener").addEventListener("click", () => {
  ejecutando = false;
  if (stream) {
    const tracks = stream.getTracks();
    tracks.forEach(track => track.stop());
    video.srcObject = null;
    resultadoCamara.textContent = "📷 Cámara detenida.";
  }
});

// Botón cambiar cámara
document.getElementById('btn-cambiar-camara').addEventListener("click", () => {
  usandoFrontal = !usandoFrontal;
  iniciarCamara();
});

// Iniciar cámara automáticamente al cargar
window.addEventListener('DOMContentLoaded', iniciarCamara);