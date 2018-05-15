$(function () {
  /* Enable editing of phrases! */
  $('main > table td[lang]').addClass('editable');

  /* Enables clicking on transcriptions/translations to change them. */
  $('.editable').click(function (evt) {
    var $el = $(evt.target);
    var field = null;
    if ($el.is('[lang=en]')) {
      field = 'translation';
    } else if ($el.is('[lang=crk]')) {
      field = 'transcription';
    } else {
      return;
    }

    var updateURI = $el.parent('[data-update-uri]').data('update-uri');
    if (!updateURI) {
      throw new Error('No update URI found for ' + event.target);
    }

    var original = $el.text();

    /* We clicked on a translation or transliteration. Ask to change it. */
    var value = prompt('Change "' + original + '" to:', original);
    if (!value) {
      return;
    }

    /* Do a PATCH to this API, sending our credentials.  */
    fetch(updateURI, {
      method: 'PATCH',
      credentials: 'same-origin',
      body: JSON.stringify({ field: field, value: value }),
      headers: {
        'Content-Type': 'application/json',
      }
    }).then(function (res) {
      /* Change the text when we get the okay from the server. */
      if (res.ok) {
        $el.text(value);
      } else {
        alert('Could not update the ' + field + ' for some reason.');
      }
    });
  });
});
/* eslint-env: browser, jquery */
/* global $ */
