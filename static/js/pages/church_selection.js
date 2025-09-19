document.addEventListener('DOMContentLoaded', function () {
    const sectorSelect = document.getElementById('sectorSelect');

    if (sectorSelect) {
        sectorSelect.addEventListener('change', function () {
            const selectedSector = this.value;

            // Hide all church lists
            const allChurchLists = document.querySelectorAll('.church-list');
            allChurchLists.forEach(list => {
                list.classList.remove('active');
            });

            // Show the selected sector's church list
            if (selectedSector) {
                const selectedChurchList = document.getElementById(selectedSector + 'Churches');
                if (selectedChurchList) {
                    selectedChurchList.classList.add('active');
                }
            }
        });
    }
});

function selectChurch(churchDomain) {
    window.location.href = `/login/${churchDomain}/`;
}
