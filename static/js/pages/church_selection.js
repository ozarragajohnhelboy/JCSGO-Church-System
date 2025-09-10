document.addEventListener('DOMContentLoaded', function () {
    const sectorSelect = document.getElementById('sectorSelect');
    const centralChurches = document.getElementById('centralChurches');
    const rizalChurches = document.getElementById('rizalChurches');

    if (sectorSelect) {
        sectorSelect.addEventListener('change', function () {
            const selectedSector = this.value;

            centralChurches.classList.remove('active');
            rizalChurches.classList.remove('active');

            if (selectedSector === 'central') {
                centralChurches.classList.add('active');
            } else if (selectedSector === 'rizal') {
                rizalChurches.classList.add('active');
            }
        });
    }
});

function selectChurch(churchDomain) {
    window.location.href = `/login/${churchDomain}/`;
}
