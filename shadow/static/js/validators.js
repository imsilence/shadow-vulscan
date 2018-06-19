
jQuery.extend(jQuery.validator.messages, {
    required: "请输入内容",
    remote: "请输入有效内容",
    email: "请输入有效的电子邮件地址",
    url: "请输入有效的网址",
    date: "请输入有效的日期",
    dateISO: "请输入有效的日期 (YYYY-MM-DD)",
    number: "请输入有效的数字",
    digits: "只能输入数字",
    creditcard: "请输入有效的信用卡号码",
    equalTo: "你的输入不相同",
    extension: "请输入有效的后缀",
    maxlength: jQuery.validator.format("最多可以输入 {0} 个字符"),
    minlength: jQuery.validator.format("最少要输入 {0} 个字符"),
    rangelength: jQuery.validator.format("请输入长度在 {0} 到 {1} 之间的字符串"),
    range: jQuery.validator.format("请输入范围在 {0} 到 {1} 之间的数值"),
    max: jQuery.validator.format("请输入不大于 {0} 的数值"),
    min: jQuery.validator.format("请输入不小于 {0} 的数值")
});

jQuery.validator.addMethod("ip", function(value, element, params) {
    var ip_regex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
        ip_range = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)-(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
        ip_cidr = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:3[0-2]|[012]?[0-9])$/,
        split_regex = /[,;\s]/,
        is_valid = true;

    value = value.split(split_regex);

    jQuery.each(value, function(k, v) {
        if(v !== '' && !ip_regex.test(v) && !ip_range.test(v) && !ip_cidr.test(v)) {
            is_valid = false;
            return false;
        }
    })

    return is_valid;
}, jQuery.validator.format("请输入有效IP地址"));


jQuery.validator.addMethod("regex", function(value, element, params) {
    return params.test(value);
}, jQuery.validator.format("请输入有效格式"));


jQuery.validator.addMethod("json", function(value, element, params) {

    try{
        var is_valid = true;
        value = jQuery.parseJSON(value);
        if(jQuery.type(params) == 'object') {
            var key_type = jQuery.type(params['keys']);
            console.log([params, key_type])
            if(key_type == 'object') {
                jQuery.each(params['keys'], function(i, v) {
                    if(jQuery.type(value[i]) != v) {
                        is_valid = false;
                        return false;
                    }
                });
            } else if(key_type == 'array') {
                jQuery.each(params['keys'], function(i, v) {
                    if(jQuery.type(value[v]) == 'undefined') {
                        is_valid = false;
                        return false;
                    }
                });
            }
        }
        return is_valid;
    } catch(e) {
        return false;
    }
}, jQuery.validator.format("请输入有效格式"));