"use strict";
const copyCitation = document.querySelector('#copy-citation');
if (copyCitation) copyCitation.addEventListener('click', async () => {
  const status = document.querySelector('#copy-status');
  try {
    await navigator.clipboard.writeText(document.querySelector('#citation-text').textContent);
    status.textContent = 'BibTeX copied.';
  } catch {
    status.textContent = 'Copy is unavailable here. Select the BibTeX above or download the .bib file.';
  }
});
