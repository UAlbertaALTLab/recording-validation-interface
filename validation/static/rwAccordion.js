let items=[];

$(function () {
    function is_base_from(key, from){
        if (key.indexOf(".",from)) {
            return key.indexOf(" ",from) < key.indexOf(".", from)
        }
        return true
    }
    function rwCategory(key,from = 0){
        return Math.min(
            [key.indexOf(".",from),key.indexOf(" ",from)].filter((x) => 0 <= x)
        )
    }

    function group_rw( items ){
        // Assumes it goes in order.
        let elements = {"children":{}};
        for (var item of items){
            let text = item.textContent.trim();
            let full_key = text.substring(0,text.indexOf(" "))
            let key = full_key.split(".")
            var place = elements
            while (key.length > 1){
                let sub = key.shift()
                place=place["children"][sub]
            }
            place["children"][key[0]]={
                "item":item,
                key: full_key,
                id: "rw-"+(full_key.split(".").join("-")),
                text: text,
                "children":{}
            }
        }
        return elements
    }

    function generate_div(elements, div){
        let children = elements["children"]
        for (var element of Object.values(children)){
            let group = $("<div />",{class:"card"}).appendTo(div)
            let base  = $("<div />",{"class":"card-header"}).appendTo(group)
            let replacement_div = $("<div />",{"class":"form-check"});
            let click = $("input",element["item"]).remove()
            click.addClass("form-check-input")
            replacement_div.append(click)
            
            $("<div />",{"id":"base-"+element["id"],"class":"form-check-label", "data-toggle":"collapse", "data-target":"#"+element["id"], "aria-expanded":"true", "aria-controls":element["id"]}).append(element["text"]).appendTo(replacement_div)
            base.append(replacement_div)
            let sub = $("<div />",{class:"collapse",id:element["id"], "aria-labelledby": "base-"+element["id"],"data-parent":"#"+div.attr("id")}).appendTo(group)
            if (Object.keys(element["children"]).length > 0){
                let child_div = $("<div />").appendTo(sub)
                generate_div(element,child_div)
            }
        }
    }
    
    $('label',$("#id_rapidwords")).each((index, element) => {
        items.push(element)
    });
    $("#id_rapidwords").addClass("accordion");
    $("#id_rapidwords").empty();

    generate_div(group_rw(items),$("#id_rapidwords"));

});