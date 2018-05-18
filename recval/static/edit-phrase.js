/**
 * Script for the phrase validation page.
 */
$(function () {
  var $forms = $('form.transcription, form.translation');
  console.assert($forms.length == 2);
  var $origin = $('form.origin');

  /* Handle the submission of the transcrption, translation forms. */
  $forms.each(function () {
    var $form = $(this);
    var $submit = $form.find('button[type=submit]');
    var $input = $form.find('input[type=text]');
    var initialValue = $input.val();

    /* Initially, disable the "change" button, as it only makes sense to change
     * it when the text has changed. */
    disableSubmitButton();

    /* When you change the text, re-enable the "change" button. */
    $input.on('keyup change', function (event) {
      if (event.target.value == initialValue) {
        disableSubmitButton();
      } else {
        enableSubmitButton();
      }
    });

    $form.submit(function (event) {
      event.preventDefault();
      var value = $input.val();

      /* Do nothing if it hasn't changed. */
      if (value == initialValue) {
        return;
      }

      var field = $input.attr('name');
      var url = $form.attr('action');
      updateField(url, field, value).then(function (res) {
        if (res.ok) {
          /* Reset the form */
          initialValue = value;
          disableSubmitButton();
        } else {
          alert('Could not perform update :(');
        }
      });
    });

    function disableSubmitButton() {
      $submit.attr('disabled', true);
    }

    function enableSubmitButton() {
      $submit.attr('disabled', false);
    }
  });

  /* Update when a radio button is selected. */
  $origin.change(function (event) {
    var url = $origin.attr('action');
    updateField(url, 'origin', event.target.value).then((res) => {
      if (!res.ok) {
        alert('Did not change value!');
      }
    });
  });


  function updateField(uri, field, value) {
    return fetch(uri, {
      method: 'PATCH',
      credentials: 'same-origin',
      body: JSON.stringify({[field]: value}),
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
});
/* eslint-env: browser, jquery */
/* global $ */
