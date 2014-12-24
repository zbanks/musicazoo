(function(exports){
    var BASE_URL = exports.BASE_URL = "";
    //var BASE_URL = "http://localhost:9000";

    // Underscore mixins

    _.mixin(_.str.exports());
    _.mixin({
        obj : function(op){
            return function(obj, fn){
                return _.chain(obj)[op](function(v, k){ return [k, fn(v)] }).object().value();
            };
        }
    });

    _.mixin({
        objectMap : _.obj("map"),
        objectFilter : _.obj("filter")
    });

    exports._ = _;

    // Handlebars extras

    Handlebars.registerHelper('minutes', function(seconds){
        var hours = Math.floor(seconds / 3600);
        seconds %= 3600;
        var minutes = Math.floor(seconds / 60);
        seconds %= 60;
        seconds = Math.floor(seconds);
        if(hours){
            return hours + ":" + _.lpad(minutes, 2, '0') + ":" + _.lpad(seconds, 2, '0');
        }else{
            return minutes + ":" + _.lpad(seconds, 2, '0');
        }
    });

    Handlebars.registerHelper('add', function(x, options){
        var v = x + parseInt(options.hash.v);
        if(!v || v < 0){
            return 0;
        }
        return v;
    });

    Handlebars.registerHelper('percent', function(x, options){
        var of = parseInt(options.hash.of);
        x = parseInt(x);
        if(of && x){
            return Math.floor(x / of * 100);
        }else{
            return 0;
        }
    });

    Handlebars.registerHelper('if_eq', function(x, options){
        if(options.hash.eq){
            if(x == options.hash.eq){
                return options.fn(this);
            }
            return options.inverse(this);
        }else{
            if(x == options.hash.neq){
                return options.inverse(this);
            }
            return options.fn(this);
        }
    });

    Handlebars.registerHelper('pressed', function(x, options){
        var list = options.hash.list;
        if(_.contains(list, x)){
            return "pressed";
        }else{
            return "";
        }
    });

    // Endpoint query wrappers

    var Endpoint = exports.Endpoint = function(url){
        this.url = url;
        this.reqs = [];
        this.alive = false;
        this.onAlive = null;
        this.onDead = null;
        this.timeout = window.setTimeout(_.bind(this.runQueries, this), 0);
    }

    Endpoint.prototype.deferQuery = function(data, cb, err){
        this.reqs.push({"data": data, "cb": cb, "err": err});
    }

    Endpoint.prototype.forceQuery = function(data, cb, err){
        this.deferQuery(data, cb, err);
        this.runQueries();
    }

    Endpoint.prototype.runQueries = function(cb, err){
        var self = this;
        if(this.timeout !== null){
            window.clearTimeout(this.timeout);
        }
        if(this.reqs.length){
            var cbs = _.pluck(this.reqs, "cb");
            var errs = _.pluck(this.reqs, "cb");
            var datas = _.pluck(this.reqs, "data");
            $.ajax(this.url, {
                data: JSON.stringify(datas),
                dataType: 'json',
                type: 'POST',
                contentType: 'text/json',
                success: function(resp){
                    self.onAlive && self.onAlive();
                    if(resp.length != datas.length){ 
                        console.error("Did not recieve correct number of responses from server!");
                        return;
                    }
                    for(var i = 0; i < resp.length; i++){
                        var r = resp[i];
                        if(!r.success){
                            console.error("Server Error:", r.error);
                            if(errs[i]){
                                errs[i]();
                            }
                        }else if(cbs[i]){
                            cbs[i](r.result);
                        }
                    }
                    if(cb){
                        cb();
                    }
                    self.timeout = window.setTimeout(function(){ self.runQueries(); }, 0); // Defer
                },
                error: function(){
                    self.onDead && self.onDead();
                    _.each(errs, function(x){ if(x){ x(); } });
                    self.timeout = window.setTimeout(function(){ self.runQueries(); }, 500); // Connection dropped?
                    if(err){
                        err();
                    }
                }
            });
        }else{
            this.timeout = window.setTimeout(function(){ self.runQueries(); }, 50);
        }
        this.reqs = [];
    }

    exports.queue_endpoint = new Endpoint(BASE_URL + "/queue");
    exports.nlp_endpoint = new Endpoint(BASE_URL + "/vol");
    exports.volume_endpoint = new Endpoint(BASE_URL + "/vol");
    exports.top_endpoint = new Endpoint(BASE_URL + "/top");

    exports.regainConnection = queue_endpoint.onAlive = function(){
        $(".disconnect-hide").show();
        $(".disconnect-show").hide();
    }

    exports.lostConnection = queue_endpoint.onDead = function (){
        console.log("Lost connection");
        $(".disconnect-show").show();
        $(".disconnect-hide").hide();
    }

    // Load settings.json

    $.getJSON("/settings.json").done(function(data){
        console.log("settings", data);
        $("html").animate({"backgroundColor": data.bg_color});
        $("html").animate({"color": data.fg_color});
        $("h1.title").text(data.name);
    });
})(window);
