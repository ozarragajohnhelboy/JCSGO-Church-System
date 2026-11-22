/**
 * Print a care group report from a modal preview.
 *
 * The report is copied into a hidden iframe and printed only after every image
 * (the JCSGO logo) has finished loading, so the logo is present in the real
 * print output and the current page is never replaced or reloaded.
 */
(function () {
    function waitForImages(doc) {
        var pending = Array.prototype.map.call(doc.images, function (image) {
            if (image.complete) {
                return Promise.resolve();
            }
            return new Promise(function (resolve) {
                image.addEventListener('load', resolve, { once: true });
                image.addEventListener('error', resolve, { once: true });
            });
        });
        return Promise.all(pending);
    }

    window.printCareGroupReport = function (button) {
        var modal = button.closest('.modal');
        var report = modal ? modal.querySelector('.print-container') : null;
        if (!report) {
            return;
        }

        var iframe = document.createElement('iframe');
        iframe.setAttribute('aria-hidden', 'true');
        iframe.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0;';
        document.body.appendChild(iframe);

        var doc = iframe.contentWindow.document;
        doc.open();
        doc.write(
            '<!DOCTYPE html><html><head><meta charset="UTF-8">' +
            '<base href="' + window.location.origin + '/">' +
            '<title>Care Group Report</title>' +
            '<style>' +
            '@page { margin: 12mm; }' +
            'body { margin: 0; font-family: Arial, sans-serif; color: #000; }' +
            'img { max-width: 100%; }' +
            '* { -webkit-print-color-adjust: exact; print-color-adjust: exact; }' +
            '</style></head><body>' + report.outerHTML + '</body></html>'
        );
        doc.close();

        var cleanup = function () {
            if (iframe.parentNode) {
                iframe.parentNode.removeChild(iframe);
            }
        };

        waitForImages(doc).then(function () {
            iframe.contentWindow.addEventListener('afterprint', cleanup);
            iframe.contentWindow.focus();
            iframe.contentWindow.print();
            setTimeout(cleanup, 60000);
        });
    };
})();
