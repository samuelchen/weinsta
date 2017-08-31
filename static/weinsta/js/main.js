    // --- Begin cross reference token for Django
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    };
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    // --- End csrf token for Django


    function css_enable(obj) {
        obj.removeAttr("disabled")
            .removeClass('disabled')
            .css("cursor", "pointer");
    }

    function css_disable(obj) {
        obj.removeAttr("disabled")
            .removeClass('disabled')
            .css("cursor", "no-drop");
    }


    // --- string funcs

    String.prototype.format = String.prototype.f = function () {
        var s = this,
            i = arguments.length;

        while (i--) {
            s = s.replace(new RegExp('\\{' + i + '\\}', 'gm'), arguments[i]);
        }
        return s;
    };

    // --- badge count change ---
    function badge_count(jq_obj, plus) {
        if (jq_obj.length <= 0)
            return;
        var t = parseInt(jq_obj.text());
        t = t + parseInt(plus);
        jq_obj.text(t);
    };


    // --- scroll a item in a container to top ---
    // --- container generally with style "overflow-y: auto; max-height: 400px;"
    // --- e.g.
    // ---      var menu_container = $('[name="lists_incl"]');
    // ---      scroll_to_item(menu_container, menu_container.find(".list-group-item.active"));

    function scroll_to_item(container, item) {
        // arguments are jquery objects
        if (container.length && item.length) {
            if (item.offset().top - container.offset().top - container.height() > 0) {
                container.animate({
                    scrollTop: item.offset().top - container.offset().top
                });
            };
        }
    };