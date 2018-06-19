var tt = null;

toastr.options = {
    "closeButton": false,
    "debug": false,
    "progressBar": true,
    "positionClass": "toast-top-center",
    "onclick": null,
    "showDuration": "400",
    "hideDuration": "1000",
    "timeOut": "10000",
    "extendedTimeOut": "1000",
    "showEasing": "swing",
    "hideEasing": "linear",
    "showMethod": "fadeIn",
    "hideMethod": "fadeOut"
};

function ajax(o) {
    var url = o['url'] || null;
    var method = o['method'] || 'POST';
    var data = o['data'] || {};
    var success = o['success'] || function(result) {
        result = result['text'] || '操作成功';
        if(tt) {
            toastr.clear(tt);
        }
        tt = toastr.success(result);
    };
    var error = o['error'] || function(error) {
        try {
            error = error || '请求错误';
            if("object" == typeof(error)) {
                var errors = [];
                jQuery.each(error, function(k, v) {
                    errors.push(v);
                });
                error = errors.join('<br />');
            }
            if(tt) {
                toastr.clear(tt);
            }
            tt = toastr.error(error);
        } catch(e) {
            console.log(e);
        }
    };
    jQuery.ajax({
        url : url,
        type : method,
        data : data,
        dataType : 'json',
        success : function(data, status, xhr) {
            switch(data['code']) {
                case 200:
                    success(data['result']);
                    break;
                case 400:
                    error(data['errors']);
                    break;
                case 403:
                    try {
                        if(tt) {
                            toastr.clear(tt);
                        }
                        tt = toastr.error(data['errors'] || '用户未登录, 请登录后重试');
                        setTimeout(function() {
                            window.location.replace('/');
                        }, 10 * 1000);
                    } catch(e) {
                        console.log(e);
                    }
                    break;
                case 500:
                    try {
                        if(tt) {
                            toastr.clear(tt);
                        }
                        tt = toastr.error(data['errors'] || '服务器错误, 请稍后再试');
                    } catch(e) {
                        console.log(e);
                    }
                    break;
            }
        },
        error : function(xhr, status, error) {

        }
    });
}