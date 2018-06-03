/*!
 * Copyright (C) 2018 Eddie Antonio Santos <easantos@ualberta.ca>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

/**
 * Script for the phrase validation page.
 */
$(function () {
  var $forms = $('form.transcription, form.translation');
  console.assert($forms.length === 2);
  var $origin = $('form.origin');
  var $recordings = $('form.recording');

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
      if (event.target.value === initialValue) {
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

  /* PATCH when a radio button for "elicitation origin" selected. */
  $origin.change(function (event) {
    var url = $origin.attr('action');
    updateField(url, 'origin', event.target.value).then((res) => {
      if (!res.ok) {
        alert('Could not change value!');
      }
    });
  });

  /* PATCH when a "clean"|"unusable" button is selected. */
  $recordings.change(function (event) {
    var url = $(this).attr('action');
    console.assert(event.target.name === 'quality');
    updateField(url, 'quality', event.target.value).then((res) => {
      if (!res.ok) {
        alert('Could not change value!');
      }
    });
  });

  /**
   * Issues a PATCH to the given URI, updating the given value.
   */
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
