            window.addEventListener('DOMContentLoaded', function () {

    // --- Gestion du rôle ---
    const roleSelect  = document.getElementById('id_role');
    const adminBlock  = document.getElementById('adminFamilyBlock');
    const memberBlock = document.getElementById('familyModal');
    console.log('roleSelect :', roleSelect);
    console.log('adminBlock :', adminBlock);
    console.log('memberBlock :', memberBlock);

    function updateRoleDisplay(role) {
        adminBlock.style.display  = role === 'admin'  ? 'block' : 'none';
        memberBlock.style.display = role === 'member' ? 'block' : 'none';
    }

    // Au chargement
    updateRoleDisplay(roleSelect.value);

    // Au changement
    roleSelect.addEventListener('change', function () {
        updateRoleDisplay(this.value);
    });

    // --- Photo de profil ---
    const photoInput = document.getElementById('id_photo');
    if (photoInput) {
        photoInput.addEventListener('change', function () {
            const label = this.closest('.file-upload').querySelector('span');
            label.textContent = this.files[0] ? this.files[0].name : 'Cliquez pour choisir une photo';
        });
    }

});

// --- Recherche famille via API ---
let searchTimeout;
function searchFamily(query) {
    clearTimeout(searchTimeout);
    if (query.length < 2) {
        document.getElementById('familyResults').innerHTML = '';
        return;
    }
    searchTimeout = setTimeout(() => {
        fetch(`/accounts/search-family/?q=${encodeURIComponent(query)}`)
            .then(r => r.json())
            .then(data => {
                const box = document.getElementById('familyResults');
                box.innerHTML = data.length === 0
                    ? '<p class="no-result">Aucune famille trouvée.</p>'
                    : data.map(f =>
                        `<div class="family-result-item" onclick="selectFamily(${f.id}, '${f.name}')">
                            <i class="fa-solid fa-house"></i> ${f.name}
                        </div>`
                    ).join('');
            });
    }, 300);
}

function selectFamily(id, name) {
    document.getElementById('familyId').value            = id;
    document.getElementById('familySelectedName').textContent = name;
    document.getElementById('familySelected').style.display  = 'flex';
    document.getElementById('familyResults').innerHTML   = '';
    document.getElementById('familySearch').value        = '';
}

function clearFamily() {
    document.getElementById('familyId').value           = '';
    document.getElementById('familySelected').style.display = 'none';
}

function togglePassword(fieldId, iconContainer) {
    const field = document.getElementById(fieldId);
    const icon  = iconContainer.querySelector('i');
    if (field.type === 'password') {
        field.type = 'text';
        icon.classList.replace('fa-eye', 'fa-eye-slash');
    } else {
        field.type = 'password';
        icon.classList.replace('fa-eye-slash', 'fa-eye');
    }
}