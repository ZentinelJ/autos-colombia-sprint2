        const VALID_USER = "demoapp";
        const VALID_PASS = "midemo1234";

        async function login() {
            const user = document.getElementById("usuario").value.trim();
            const pass = document.getElementById("password").value;
            const err = document.getElementById("error-msg");
            err.style.display = "none";

            if (user === VALID_USER && pass === VALID_PASS) {
                localStorage.setItem("rol", "superadmin");
                localStorage.setItem("login", user);
                localStorage.setItem("nombres", "Super Admin");
                window.location.href = "app.html";
            } else {
                try {
                    const res = await fetch("http://localhost:8000/usuario/login", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ login: user, password: pass })
                    });
                    const data = await res.json();
                    
                    if (res.ok) {
                        localStorage.setItem("rol", data.rol);
                        localStorage.setItem("login", data.login);
                        localStorage.setItem("nombres", data.nombres);
                        window.location.href = "app.html";
                    } else {
                        err.textContent = data.detail || "Usuario o contraseña incorrectos.";
                        err.style.display = "block";
                    }
                } catch (e) {
                    err.textContent = "Error de conexión con el servidor.";
                    err.style.display = "block";
                }
            }
        }

        document.getElementById("password").addEventListener("keydown", e => {
            if (e.key === "Enter") login();
        });
