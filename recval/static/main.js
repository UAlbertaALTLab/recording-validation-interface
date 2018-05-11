$(function () {
  $('main > table').click(function (evt) {
    var $el = $(evt.target);
    var field;
    field = $el.is('[lang=en]') && 'translation';
    field = field || ($el.is('[lang=crk]') && 'transcription');

    if (!field) {
      return;
    }

    var updateURI = $el.parent('[data-update-uri]').data('update-uri');

    if (!updateURI) {
      console.error('No update URI found for ', event.target);
      return;
    }

    var original = $el.text();

    /* We clicked on a translation or transliteration. Ask to change it. */
    var value = prompt('Change "' + original + '" to:', original);
    if (!value) {
      return;
    }

    /**
     * Do a PATCH to this API, with our credentials.
     */
    fetch(updateURI, {
      method: 'PATCH',
      credentials: 'same-origin',
      body: JSON.stringify({ field: field, value: value }),
      headers: {
        'Content-Type': 'application/json',
      }
    }).then(function (res) {
      if (res.ok) {
        $el.text(value);
      } else {
        alert('Could not change text for some reason.');
      }
    });
  });
});
/* eslint-env: browser, jquery */
/* global $ */
