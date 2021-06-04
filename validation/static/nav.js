"use strict";

document.addEventListener("DOMContentLoaded", () => {
    for (let b of document.querySelectorAll('[data-cy="go-button-nav"]')) {
        b.addEventListener("click", (e) => {
            let pageNo = document.querySelector('[data-cy="page-num-input"]').value;
            console.log(pageNo);
            let prevPageNo = getUriComponent("page");
            let loc = window.location.search;
            if (loc && prevPageNo) {
                let prevPage = "page=" + prevPageNo;
                let newPage = "page=" + pageNo;
                loc = loc.replace(prevPage, newPage);
            } else if (loc) {
                loc += "&page=" + pageNo;
            } else {
                loc += "?page=" + pageNo;
            }

            window.location = loc;
        })
    }
})

// https://stackoverflow.com/questions/831030/how-to-get-get-request-parameters-in-javascript
function getUriComponent(name){
   if(name=(new RegExp('[?&]'+encodeURIComponent(name)+'=([^&]*)')).exec(location.search))
      return decodeURIComponent(name[1]);
}
