        const API = "http://localhost:8000";

        async function apiCall(method, path, body = null) {
            const opts = { method, headers: { "Content-Type": "application/json" } };
            if (body) opts.body = JSON.stringify(body);
            try {
                const res = await fetch(API + path, opts);
                const data = await res.json();
                return { ok: res.ok, data };
            } catch (err) {
                return { ok: false, data: { detail: "Error de conexión con el servidor." } };
            }
        }

        function ocultarMensajes(sec) {
            ['error', 'ok'].forEach(t => {
                const el = document.getElementById(`${t}-${sec}`);
                if (el) el.style.display = 'none';
            });
        }

        function mostrarError(sec, msg) {
            const el = document.getElementById(`error-${sec}`);
            if (el) {
                el.textContent = msg; 
                el.style.display = 'block';
            }
        }

        function mostrarOk(sec, msg) {
            const el = document.getElementById(`ok-${sec}`);
            if (el) {
                el.textContent = msg; 
                el.style.display = 'block';
            }
        }

        function limpiarInput(id) {
            const target = document.getElementById(id);
            if (target) target.value = '';
        }

        function mostrarSeccion(id) {
            document.querySelectorAll('.seccion').forEach(s => s.style.display = 'none');
            const target = document.getElementById(id);
            if(target) target.style.display = 'flex';
            
            if (id === 'dashboard') {
                cargarDashboard();
            } else if (id === 'usuarios') {
                mostrarSubSeccion('nuevo-operario', 'usuarios');
            } else if (id === 'celdas') {
                mostrarSubSeccion('registrar-celda', 'celdas');
            }
        }

        function mostrarSubSeccion(id, parentId) {
            document.querySelectorAll('.sub-seccion-' + parentId).forEach(s => s.style.display = 'none');
            const target = document.getElementById(id);
            if(target) target.style.display = 'flex';
            
            ocultarMensajes(parentId);
            ocultarMensajes(id);
            
            if (id === 'consultar-usuarios') {
                document.getElementById('busq-usuario').value = '';
                buscarUsuarios();
            } else if (id === 'dashboard-celdas') {
                cargarDashboardCeldas();
            }
        }

        // INIT
        window.onload = () => { 
            const rol = localStorage.getItem("rol");
            if (!rol) {
                window.location.href = "login.html";
                return;
            }
            if (rol === "operario") {
                const itemUsuarios = document.getElementById("menu-usuarios");
                const itemCeldas = document.getElementById("menu-celdas");
                if (itemUsuarios) itemUsuarios.style.display = "none";
                if (itemCeldas) itemCeldas.style.display = "none";
            }
            mostrarSeccion('dashboard'); 
        };

        function salir() {
            localStorage.removeItem("rol");
            localStorage.removeItem("login");
            localStorage.removeItem("nombres");
            window.location.href = "login.html";
        }

        // --- DASHBOARD ---
        async function cargarDashboard() {
            const tbody = document.getElementById('tabla-dashboard');
            tbody.innerHTML = '';
            
            const resActivos = await apiCall('GET', '/registro/activos');
            if (!resActivos.ok) return;
            const activos = resActivos.data;

            const resNovedades = await apiCall('GET', '/novedad/activos');
            const novedades = resNovedades.ok ? resNovedades.data : [];



            activos.forEach(reg => {
                const nov = novedades.find(n => n.id_registro === reg.id_registro);
                let desc = "N/A";
                if (nov) {
                    desc = nov.descripcion.length > 30 ? nov.descripcion.substring(0, 30) + '...' : nov.descripcion;
                }

                const fechaIn = new Date(reg.fecha_entrada).toLocaleString('es-CO', {dateStyle:'short', timeStyle:'short'});

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${reg.placa_vehiculo}</td>
                    <td style="font-weight: bold; color: #4472a8;">${reg.celda ? reg.celda : '-'}</td>
                    <td>${fechaIn}</td>
                    <td>${desc}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        // --- ENTRADA ---
        async function registrarEntrada() {
            const placa = document.getElementById("placa-entrada").value.trim();
            ocultarMensajes('entrada');
            if (placa.length !== 6) {
                mostrarError('entrada', "La placa debe tener exactamente 6 caracteres.");
                return;
            }
            // 1. Asegurar vehículo
            await apiCall('POST', '/vehiculo', { placa, marca: 'Desconocido', modelo: 'Desconocido' });
            // 2. Registrar entrada
            const { ok, data } = await apiCall('POST', '/registro/entrada', { placa_vehiculo: placa });
            if (!ok) mostrarError('entrada', data.detail);
            else { 
                mostrarOk('entrada', `Entrada registrada para ${placa}.`); 
                limpiarInput('placa-entrada'); 
            }
        }

        // --- SALIDA ---
        async function registrarSalida() {
            const placa = document.getElementById("placa-salida").value.trim();
            ocultarMensajes('salida');
            if (placa.length !== 6) {
                mostrarError('salida', "La placa debe tener exactamente 6 caracteres.");
                return;
            }
            const { ok, data } = await apiCall('POST', '/registro/salida', { placa_vehiculo: placa });
            if (!ok) mostrarError('salida', data.detail);
            else { 
                mostrarOk('salida', `Salida registrada para ${placa}.`); 
                limpiarInput('placa-salida'); 
            }
        }

        // --- NOVEDADES ---
        async function buscarParaNovedad() {
            const placa = document.getElementById("placa-novedad").value.trim();
            ocultarMensajes('novedad');
            const txt = document.getElementById("desc-novedad");
            const btn = document.getElementById("btn-registrar-novedad");
            
            txt.disabled = true;
            btn.disabled = true;
            txt.value = '';

            if (placa.length !== 6) {
                mostrarError('novedad', 'La placa debe tener 6 caracteres.');
                return;
            }

            const { ok, data } = await apiCall('GET', '/vehiculo/' + placa);
            if (!ok) {
                mostrarError('novedad', 'La placa ingresada no existe en el sistema.');
            } else {
                txt.disabled = false;
                btn.disabled = false;
                txt.focus();
            }
        }

        async function registrarNovedad() {
            const placa = document.getElementById("placa-novedad").value.trim();
            const desc = document.getElementById("desc-novedad").value.trim();
            ocultarMensajes('novedad');
            if (!desc) {
                mostrarError('novedad', 'La descripción no puede estar vacía.');
                return;
            }
            const { ok, data } = await apiCall('POST', '/novedad', { placa_vehiculo: placa, descripcion: desc });
            if (!ok) mostrarError('novedad', data.detail);
            else { 
                mostrarOk('novedad', 'Novedad registrada correctamente.'); 
                document.getElementById("desc-novedad").value = ''; 
                document.getElementById("desc-novedad").disabled = true;
                document.getElementById("btn-registrar-novedad").disabled = true;
                limpiarInput('placa-novedad');
            }
        }

        // --- HISTORIAL ---
        function calcularDuracion(entrada, salida) {
            const diff = Math.floor((new Date(salida) - new Date(entrada)) / 60000);
            return `${Math.floor(diff/60)}h ${String(diff%60).padStart(2,'0')}mn`;
        }

        async function buscarHistorial() {
            const placa = document.getElementById("placa-historial").value.trim();
            const tbody = document.getElementById("tabla-historial");
            tbody.innerHTML = '';
            
            if (placa.length !== 6) return;

            const { ok, data } = await apiCall('GET', '/registro/historial/' + placa);
            if (!ok) return;

            if (data.length === 0) {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td colspan="3" style="text-align:center;">No se encontraron registros para esta placa.</td>`;
                tbody.appendChild(tr);
                return;
            }

            data.forEach(row => {
                const fEntrada = new Date(row.fecha_entrada).toLocaleString('es-CO');
                const fSalida = new Date(row.fecha_salida).toLocaleString('es-CO');
                const pDuracion = calcularDuracion(row.fecha_entrada, row.fecha_salida);

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${fEntrada}</td>
                    <td>${fSalida}</td>
                    <td>${pDuracion}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        // --- USUARIOS ---
        async function buscarUsuarios() {
            const q = document.getElementById("busq-usuario").value.trim();
            ocultarMensajes('usuarios');
            const tbody = document.getElementById("tabla-usuarios");
            tbody.innerHTML = '';
            document.getElementById("msg-consulta-usuarios").textContent = '';

            let path = '/usuario/todos';
            if (q) path = '/usuario/buscar?q=' + encodeURIComponent(q);

            const { ok, data } = await apiCall('GET', path);
            if (!ok) {
                mostrarError('usuarios', data.detail);
                return;
            }

            if (data.length === 0) {
                document.getElementById("msg-consulta-usuarios").textContent = q ? 'NO SE HAN ENCONTRADO RESULTADOS' : 'NO HAY USUARIOS REGISTRADOS';
                return;
            }

            data.forEach(u => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${u.nombres}</td>
                    <td>${u.dni}</td>
                    <td>${u.movil}</td>
                    <td>${u.rol.toUpperCase()}</td>
                    <td>
                        <button class="btn-icon" style="width:35px;height:35px;font-size:1rem;background-color:#5583b9;display:inline-flex;margin-right:5px;" onclick="abrirEditarUsuario('${u.dni}')">✎</button>
                        <button class="btn-icon" style="width:35px;height:35px;font-size:1rem;background-color:#c07070;display:inline-flex;" onclick="abrirEliminarUsuario('${u.dni}', '${u.nombres}')">🗑</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        async function abrirEditarUsuario(dni) {
            ocultarMensajes('editar-usuario');
            const { ok, data } = await apiCall('GET', '/usuario/' + dni);
            if (!ok) return;
            document.getElementById('edit-doc').value = data.dni;
            document.getElementById('edit-nombre').value = data.nombres;
            document.getElementById('edit-tel').value = data.movil;
            document.getElementById('edit-correo').value = data.correo;
            document.getElementById('edit-rol').value = data.rol;
            
            if (data.rol === 'operario') {
                document.getElementById('edit-op-fields').style.display = 'flex';
                document.getElementById('edit-cli-vehiculos').style.display = 'none';
                document.getElementById('edit-usuario').value = data.login;
                document.getElementById('edit-pass').value = '';
            } else {
                document.getElementById('edit-op-fields').style.display = 'none';
                document.getElementById('edit-cli-vehiculos').style.display = 'flex';
                cargarVehiculosCliente(dni);
            }
            mostrarSubSeccion('editar-usuario', 'usuarios');
        }

        function cerrarEdicionUsuario() {
            mostrarSubSeccion('consultar-usuarios', 'usuarios');
        }

        async function guardarEdicionUsuario() {
            const dni = document.getElementById('edit-doc').value;
            const rol = document.getElementById('edit-rol').value;
            const body = {
                nombres: document.getElementById('edit-nombre').value.trim(),
                movil: document.getElementById('edit-tel').value.trim(),
                correo: document.getElementById('edit-correo').value.trim()
            };
            if (rol === 'operario') {
                body.login = document.getElementById('edit-usuario').value.trim();
                const pass = document.getElementById('edit-pass').value;
                if (pass) body.password = pass;
            }

            const { ok, data } = await apiCall('PUT', '/usuario/' + dni, body);
            if (!ok) {
                mostrarError('editar-usuario', data.detail);
            } else {
                cerrarEdicionUsuario();
                buscarUsuarios();
                mostrarOk('usuarios', 'Usuario actualizado correctamente.');
            }
        }

        async function cargarVehiculosCliente(dni) {
            const tbody = document.getElementById('tabla-vehiculos-cliente');
            tbody.innerHTML = '';
            const { ok, data } = await apiCall('GET', '/vehiculo/cliente/' + dni);
            if (!ok) return;
            
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td style="text-align:center; color:gray;">EL CLIENTE NO TIENE VEHÍCULOS</td></tr>';
                return;
            }
            
            data.forEach(v => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="text-align:center; font-weight:bold; font-size:1.2rem;">${v}</td>
                    <td style="text-align:center;">
                        <button class="btn-icon" style="width:35px;height:35px;font-size:1rem;background-color:#c07070;display:inline-flex;" onclick="eliminarVehiculoCliente('${v}', '${dni}')">🗑</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        async function agregarVehiculoCliente() {
            ocultarMensajes('editar-usuario');
            const dni = document.getElementById('edit-doc').value;
            const placa = document.getElementById('nueva-placa-cliente').value.trim();
            const marca = document.getElementById('nueva-marca-cliente').value.trim();
            const modelo = document.getElementById('nuevo-modelo-cliente').value.trim();

            if (!placa || !marca || !modelo) {
                mostrarError('editar-usuario', 'Todos los campos son obligatorios.');
                return;
            }
            if (placa.length !== 6) {
                mostrarError('editar-usuario', 'La placa debe tener 6 caracteres.');
                return;
            }
            const body = { placa, marca, modelo, dni_cliente: dni };
            const { ok, data } = await apiCall('POST', '/vehiculo', body);
            if (!ok) {
                mostrarError('editar-usuario', data.detail);
            } else {
                mostrarOk('editar-usuario', 'Vehículo agregado exitosamente.');
                document.getElementById('nueva-placa-cliente').value = '';
                document.getElementById('nueva-marca-cliente').value = '';
                document.getElementById('nuevo-modelo-cliente').value = '';
                cargarVehiculosCliente(dni);
            }
        }

        async function eliminarVehiculoCliente(placa, dni) {
            ocultarMensajes('editar-usuario');
            const { ok, data } = await apiCall('DELETE', '/vehiculo/' + placa);
            if (!ok) {
                mostrarError('editar-usuario', data.detail || 'Error al eliminar el vehículo.');
            } else {
                mostrarOk('editar-usuario', 'Vehículo eliminado correctamente.');
                cargarVehiculosCliente(dni);
            }
        }

        function abrirEliminarUsuario(dni, nombre) {
            ocultarMensajes('usuarios');
            document.getElementById('borrar-user-doc').value = dni;
            document.getElementById('borrar-user-nombre').textContent = nombre;
            document.getElementById('modal-eliminar-usuario').style.display = 'block';
            document.getElementById('modal-editar-usuario').style.display = 'none';
            document.getElementById('modal-eliminar-usuario').scrollIntoView({behavior: "smooth"});
        }

        function cancelarBorrarUsuario() {
            document.getElementById('modal-eliminar-usuario').style.display = 'none';
        }

        async function confirmarBorrarUsuario() {
            const dni = document.getElementById('borrar-user-doc').value;
            const { ok, data } = await apiCall('DELETE', '/usuario/' + dni);
            if (!ok) {
                mostrarError('usuarios', data.detail);
            } else {
                mostrarOk('usuarios', 'Usuario eliminado correctamente.');
                cancelarBorrarUsuario();
                buscarUsuarios();
            }
        }

        async function registrarOperario() {
            ocultarMensajes('nuevo-operario');
            const body = {
                nombres: document.getElementById('op-nombre').value.trim(),
                dni: document.getElementById('op-doc').value.trim(),
                movil: document.getElementById('op-tel').value.trim(),
                correo: document.getElementById('op-correo').value.trim(),
                login: document.getElementById('op-usuario').value.trim(),
                password: document.getElementById('op-pass').value
            };
            
            if (!body.nombres || !body.dni || !body.movil || !body.correo || !body.login || !body.password) {
                mostrarError('nuevo-operario', 'Todos los campos son obligatorios.');
                return;
            }
            if (body.dni.length !== 10) {
                mostrarError('nuevo-operario', 'El documento debe tener 10 caracteres.');
                return;
            }
            if (body.password.length < 6) {
                mostrarError('nuevo-operario', 'La contraseña debe tener mínimo 6 caracteres.');
                return;
            }

            const { ok, data } = await apiCall('POST', '/usuario/operario', body);
            if (!ok) mostrarError('nuevo-operario', data.detail);
            else {
                mostrarOk('nuevo-operario', 'Operario registrado correctamente.');
                ['op-nombre', 'op-doc', 'op-tel', 'op-correo', 'op-usuario', 'op-pass'].forEach(limpiarInput);
            }
        }

        async function registrarCliente() {
            ocultarMensajes('nuevo-cliente');
            const body = {
                nombres: document.getElementById('cli-nombre').value.trim(),
                dni: document.getElementById('cli-doc').value.trim(),
                movil: document.getElementById('cli-tel').value.trim(),
                correo: document.getElementById('cli-correo').value.trim(),
                placa: document.getElementById('cli-placa').value.trim(),
                marca: document.getElementById('cli-marca').value.trim(),
                modelo: document.getElementById('cli-modelo').value.trim()
            };
            
            if (!body.nombres || !body.dni || !body.movil || !body.correo || !body.placa || !body.marca || !body.modelo) {
                mostrarError('nuevo-cliente', 'Todos los campos son obligatorios.');
                return;
            }
            if (body.dni.length !== 10) {
                mostrarError('nuevo-cliente', 'El documento debe tener 10 caracteres.');
                return;
            }
            if (body.placa.length !== 6) {
                mostrarError('nuevo-cliente', 'La placa debe tener 6 caracteres.');
                return;
            }

            const { ok, data } = await apiCall('POST', '/usuario/cliente', body);
            if (!ok) mostrarError('nuevo-cliente', data.detail);
            else {
                mostrarOk('nuevo-cliente', 'Cliente registrado correctamente.');
                ['cli-nombre', 'cli-doc', 'cli-tel', 'cli-correo', 'cli-placa', 'cli-marca', 'cli-modelo'].forEach(limpiarInput);
            }
        }

        // --- CELDAS ---
        async function registrarCelda() {
            ocultarMensajes('registrar-celda');
            const id = document.getElementById('celda-id').value.trim();
            if (!id) {
                mostrarError('registrar-celda', 'El identificador no puede estar vacío.');
                return;
            }
            const { ok, data } = await apiCall('POST', '/celda', { identificador: id });
            if (!ok) mostrarError('registrar-celda', data.detail);
            else {
                mostrarOk('registrar-celda', 'Celda registrada correctamente.');
                limpiarInput('celda-id');
                // update dashboard celdas quietly
                cargarDashboard();
            }
        }

        async function generarRangoCeldas() {
            ocultarMensajes('registrar-celda');
            const prefijo = document.getElementById('celda-rango-prefijo').value.trim();
            const desdeStr = document.getElementById('celda-rango-desde').value.trim();
            const hastaStr = document.getElementById('celda-rango-hasta').value.trim();
            
            if (!prefijo || !desdeStr || !hastaStr) {
                mostrarError('registrar-celda', 'Todos los campos de rango son obligatorios.');
                return;
            }

            const desde = parseInt(desdeStr, 10);
            const hasta = parseInt(hastaStr, 10);

            if (isNaN(desde) || isNaN(hasta)) {
                mostrarError('registrar-celda', 'DESDE y HASTA deben ser numéricos.');
                return;
            }

            if (desde > hasta) {
                mostrarError('registrar-celda', 'El valor DESDE debe ser menor o igual a HASTA.');
                return;
            }

            const { ok, data } = await apiCall('POST', '/celda/rango', { prefijo, desde, hasta });
            if (!ok) {
                mostrarError('registrar-celda', data.detail || 'Error al generar celdas.');
            } else {
                if (data.saltadas > 0) {
                    mostrarError('registrar-celda', data.mensaje);
                } else {
                    mostrarOk('registrar-celda', data.mensaje);
                }
                limpiarInput('celda-rango-prefijo');
                limpiarInput('celda-rango-desde');
                limpiarInput('celda-rango-hasta');
                cargarDashboard();
            }
        }

        async function cargarDashboardCeldas() {
            ocultarMensajes('celdas');
            document.getElementById('msg-consulta-celdas').textContent = '';
            const tbody = document.getElementById("tabla-celdas");
            tbody.innerHTML = '';
            
            const { ok, data } = await apiCall('GET', '/celda/todas');
            if (!ok) return;

            document.getElementById('celda-total').textContent = data.totales.total;
            document.getElementById('celda-ocupadas-val').textContent = data.totales.ocupadas;
            document.getElementById('celda-disponibles-val').textContent = data.totales.disponibles;

            if (data.celdas.length === 0) {
                document.getElementById('msg-consulta-celdas').textContent = 'NO HAY CELDAS CONFIGURADAS EN EL SISTEMA';
                return;
            }

            data.celdas.forEach(c => {
                const tr = document.createElement('tr');
                const estadoTxt = c.disponible ? 'LIBRE' : 'OCUPADA';
                const estadoColor = c.disponible ? '#a8d5a2' : '#c07070';
                const placa = c.placa ? c.placa : '-';
                
                let btnHtml = '';
                if (c.disponible) {
                    btnHtml = `<button class="btn-icon" style="width:35px;height:35px;font-size:1rem;background-color:#c07070;display:inline-flex;" onclick="abrirEliminarCelda('${c.identificador}')">🗑</button>`;
                }
                
                tr.innerHTML = `
                    <td>${c.identificador}</td>
                    <td style="background-color: ${estadoColor}; font-weight: bold; text-align: center; color: #2e3f5c;">${estadoTxt}</td>
                    <td>${placa}</td>
                    <td>${btnHtml}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        function abrirEliminarCelda(id) {
            ocultarMensajes('celdas');
            document.getElementById('borrar-celda-id').textContent = id;
            document.getElementById('modal-eliminar-celda').style.display = 'block';
            document.getElementById('modal-eliminar-celda').scrollIntoView({behavior: "smooth"});
        }

        function cancelarBorrarCelda() {
            document.getElementById('modal-eliminar-celda').style.display = 'none';
        }

        async function confirmarBorrarCelda() {
            const id = document.getElementById('borrar-celda-id').textContent;
            const { ok, data } = await apiCall('DELETE', '/celda/' + id);
            if (!ok) {
                mostrarError('celdas', data.detail);
            } else {
                mostrarOk('celdas', 'Celda eliminada correctamente.');
                cancelarBorrarCelda();
                cargarDashboardCeldas();
                cargarDashboard();
            }
        }
