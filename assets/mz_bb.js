var volume_lockout = false;
setInterval(function(){ volume_lockout = false; }, 500);

var _query_queue = [];
var _runquery_timeout;
var BASE_URL = "http://localhost:9000/";

function deferQuery(data, cb, err){
    //TODO: err does nothing
    _query_queue.push({"data": data, "cb": cb, "err": err});
}

function forceQuery(data, cb, err){
    deferQuery(data, cb, err);
    runQueries();
}

function runQueries(cb){
    window.clearTimeout(_runquery_timeout);
    if(_query_queue.length){
        var cbs = _.pluck(_query_queue, "cb");
        var errs = _.pluck(_query_queue, "cb");
        var datas = _.pluck(_query_queue, "data");
        $.post(BASE_URL, JSON.stringify(datas), function(resp){
            if(resp.length != datas.length){ 
                console.error("Did not recieve correct number of responses from server!");
                return;
            }
            for(var i = 0; i < resp.length; i++){
                var r = resp[i];
                if(!r.success){
                    console.log(r.error);
                }else if(cbs[i]){
                    cbs[i](r.result);
                }
            }
            if(cb){
                cb();
            }
            _runquery_timeout = window.setTimeout(runQueries, 0); // Defer
        }, 'json');
    }else{
        _runquery_timeout = window.setTimeout(runQueries, 50);
    }
    _query_queue = [];
}

function authenticate(cb){
    // Auth & get capabilities
    forceQuery({cmd: "capabilities"}, function(cap){
        cb(cap);
    });
}

/*
// http://www.knockmeout.net/2011/05/dragging-dropping-and-sorting-with.html
//connect items with observableArrays
ko.bindingHandlers.sortableList = {
  init: function(element, valueAccessor) {
      var list = valueAccessor();
      $(element).sortable({
          update: function(event, ui) {
              //retrieve our actual data item
              var item = ui.item.tmplItem().data;
              //figure out its new position
              var position = ko.utils.arrayIndexOf(ui.item.parent().children(), ui.item[0]);
              //remove the item and add it back in the right spot
              if (position >= 0) {
                  list.remove(item);
                  list.splice(position, 0, item);
              }
          }
      });
  }
};
*/

$(document).ready(function(){
    $(".uploadFile").submit(function(){
        $(".queueform");
    });
    
/*
    $("input.addtxt").keyup(function(){
        var query = $(this).val();
        if(query == ""){
            $(".results").html("");
            return;
        }
        var ytrequrl = "http://gdata.youtube.com/feeds/api/videos?v=2&orderby=relevance&alt=jsonc&q=" + encodeURIComponent(query) + "&max-results=5&callback=?"
        $.getJSON(ytrequrl, function(data){
            var list = $("<ol class='suggest'></ol>");
            var i = 0;
            var index = query.indexOf(" ");

            if(index == -1){
                cmd_ = "";
                cmd = query.toLowerCase();
            }else{
                var cmd_ = query.substr(index);
                var cmd = query.substr(0, index).toLowerCase();
            }
            
            var isCmdPrefix = function(prefix){
                if(cmd.length < prefix.length){
                    return cmd == prefix.substr(0, cmd.length);
                }
                if(cmd.length == 0){
                    return false;
                }
                return cmd == prefix
            }

            for(var j = 0; j < window.commands.length && i < 5; j++){
                var c = window.commands[j];
                console.log(c, cmd);

                if(isCmdPrefix(c)){
                    console.log(c, cmd_);
                    list.append($("<a href='/add/" + c + "+" + cmd_ + "'><li><strong>" + c + "</strong>" + cmd_ + "</li></a>"));
                    i++
                }
            }

            for(var j = 0; j < data.data.items.length && j + i < 5; j++){
                var vid = data.data.items[j];
                list.append($("<a href='/add/youtube/" + vid.id + "'><li>" + vid.title + "</li></a>"));
            }
            $(".results").html("").append(list);
        });
        return true;
    });

    $(".queueform").submit(function(){
        if($("input[type=file]").val()){
            return;
        }
        var query = $(".addtxt").val();
        if(!query){
            return false;
        }
        $(".addtxt").val("");
        $.post("/add/" + encodeURIComponent(query),  function(data){
            console.log(data);
            if(!data.success){
                $("div.error").html(data.error).show(300, function(){
                    setTimeout(5000, function(){
                        $("div.error").hide(200);
                    });
                });
            }
            refreshPlaylist();
            $(".addtxt").val("");
        });
        return false; // Prevent form submitting
    });

    */
    
        /*
    $("ol.playlist").sortable({
        update: function(ev, ui){
            var ordering = $("ol.playlist li").map(function(i, e){return $(e).attr('id')}).toArray().join(";");
            var url = "/msg?queue_cmd=mv&ordering=" + ordering;
            $.get(url);
        },
        start: function(ev, ui){
            window.no_autorefresh = true;
        },
        stop: function(ev, ui){
            window.no_autorefresh = false;
        }
    });
    */

});

var loadSlider = function(){
    $("div.vol-slider").slider({
        orientation: "horizontal",
        range: "min",
        min: 0,
        max: 100,
        value: window.volume,
        slide: function(ev, ui) {
            updateSlider(ui.value);
            if(volume_lockout)
                return;
            volume_lockout = true;
            console.log(ui.value);
            console.log("???");
            //deferQuery({"cmd": "set_vol", "args": [ui.value], "target": vm.statics().volume.uid() }, function(){ volume_lockout = false; });
            //console.log({"cmd": "set_vol", "args": [ui.value]});
            /*
            $.get("/vol/" + ui.value, function(){
                volume_lockout = false;   
            });
            */
        }
    });
    updateSlider(window.volume);
}

var updateSlider = function(value){
    console.log(value);
    $("div.vol-slider").slider("option", "value", value);
    $(".ui-slider-range").html("<span>" + value + "</span>");
}



/*
var MODULES = {
    "youtube" : {
        _params: ["url"],
        _template: "youtube",
        _template_act: "youtube_act"
    }
};

var STATICS = {
    "volume" : {
        _template: "volume",
        _params: ["vol"],
        create: function(options){
            return ko.mapping.fromJS(options.data, {}, this);
        }
    }
};
*/


/*
function Musicazoo() { 
    var self = this;
    self.MODULES = MODULES;
    self.STATICS = STATICS;
    // The following are sub View-Models
    self.queue = ko.observable([]);
    self.activeq = ko.observable([]);
    self.statics = ko.observable({volume: {vol: ko.observable(0)}}); 
    self.statics().volume.vol.subscribe(updateSlider);

    self.reload = function() {
        if(window.no_autorefresh) return;
        var fetch_params = function(defs){
            return function(q){
                if(defs[q.type]){
                    _.each(defs[q.type]._params, function(mp){
                        deferQuery({"cmd": "get_" + mp, "target": q.uid}, function(v){
                            q[mp] = v; 
                        });
                    });
                }else{
                    console.log("Unknown static/module: " + q.type);
                }
            };
        }

        deferQuery({"cmd": "queue"}, function(queue_list) {
            _.each(queue_list, fetch_params(self.MODULES));

            runQueries(function(){
                console.log("Loaded queue:");
                console.log(queue_list);
                ko.mapping.fromJS(queue_list, {}, self.queue);
                $("ol.playlist").sortable("refresh");
            });

        });
        deferQuery({"cmd": "cur"}, function(queue_cur_list) {
            _.each(queue_cur_list, fetch_params(self.MODULES));

            runQueries(function(){
                console.log("Loaded current queue:");
                console.log(queue_cur_list);
                ko.mapping.fromJS(queue_cur_list, {}, self.activeq);
            });

        });
        deferQuery({"cmd": "statics"}, function(statics_list) {
            _.each(statics_list, fetch_params(self.STATICS));
            
            runQueries(function(){
                var _sts = {};
                for(var i = 0; i < statics_list.length; i++){
                    _sts[statics_list[i].type] = statics_list[i];
                }
                //updateSlider(statics.volume.vol)
                //console.log(_sts);
                ko.mapping.fromJS(_sts, self.STATICS, self.statics);
                //self.statics().volume.vol.subscribe(function(nv){ console.log("VOL HIT"); console.log(nv); });
                //self.statics().volume.vol_test = ko.computed(function(){ return self.statics().volume.vol(); });
            });
        });
    };
};  
*/

var TEMPLATE_NAMES = {"youtube": {queue: "youtube", active: "youtube_active"} };
var TEMPLATES = _.chain({
    "youtube": '<a href="{{ url }}">{{ url }}</a>',
    "youtube_active": '<a href="{{ url }}">{{ url }}</a>',
    "unknown": '(Unknown)',
    "unknown": '(Unknown)',
}).map(function(v, k){ return [k, Handlebars.compile(v)] }).object().value();

var QUEUE_TEMPLATE = Handlebars.compile('{{#each this}}\n<li>{{{this}}}</li>{{/each}}');


authenticate(function(capabilities){
    var modules = capabilities;//.modules; // We care about everything
    var statics = {}; capabilities.statics;
    var module_capabilities = _.chain(modules).map(function(v, k){ return [k, v.parameters] }).object().value();
    console.log(capabilities);
    console.log(module_capabilities);
    Backbone.sync = function(method, model, options){
        /*
        if(method == "read"){
            _.each(model.parameters, function(k){
                deferQuery({cmd: "get_" + k, target: model.id}, function(v){
                    model.set(k, v); 
                });
            });
        }else if(method == "update"){
            _.each(model.parameters, function(k){
                if(model.hasChanged(k)){
                    deferQuery({cmd: "set_" + k, target: model.id, args: [model.get(k)]});
                }
            });
        }else if(method == "delete"){
            deferQuery({cmd: "rm", target: 0, args: [model.id]});
        }else if(method == "create"){
            //TODO
            console.log("Can't create");
            deferQuery({cmd: "add"});
        }
        runQueries(function(){
            options.success(model)
        });
        return true;
        */
        console.error("unsupported sync");
        console.log(method, model, options);
    }
        



    var Action = Backbone.Model.extend({
        defaults: function(){
            return {
                type: null,
            };
        },
        parse: function(resp, options){
            var attrs = {type: resp.type, uid: resp.uid};
            _.each(resp.parameters, function(v, k){ attrs[k] = v; });

            if(TEMPLATES[resp.type]){
                this.template_queue = TEMPLATE_NAMES[resp.type].queue;
                this.template_active = TEMPLATE_NAMES[resp.type].active;
            }else{
                this.template_queue = "unknown";
                this.template_active = "unknown";
            }
            
            this.parameters = modules[resp.type].parameters;
            this.commands = modules[resp.type].commands;
            return attrs;
        },
        idAttribute: "uid",
        parameters: [],
        commands: [],
        template_queue: "unknown",
        template_active: "unknown",
        active: false
    });

    var CurrentAction = Action.extend({
        sync: function(method, model, options){
            if(method != "read"){
                console.error("Can only read from CurrentAction");
                return;
            }
            deferQuery({cmd: "cur", args: [module_capabilities]}, options.success);
        },
        active: true
    });

    var Queue = Backbone.Collection.extend({
        model: Action,
        parse: function(resp, options){
            console.log("queue parse");
            console.log(resp);
            return resp;
        },
        sync: function(method, model, options){
            if(method != "read"){
                console.error("Can only read from Queue");
                return;
            }
            deferQuery({cmd: "queue", args: [module_capabilities]}, options.success);
        }
    });
    
    /*
    _.each(modules, function(v, k){
        modules[k].Model = Action.extend({
            type: k,
            parameters: function(){
                return v.parameters;
            },
            commands: function(){
                return v.commands;
            }
        });
    });
    */

    var Static = Backbone.Model.extend({
        defaults: function(){
            return {

            };
        },
        parse: function(resp, options){
            console.log("static parse");
            console.log(resp);
        },
        idAttribute: "uid",
        parameters: [],
        commands: []
    });
    
    var StaticSet = Backbone.Collection.extend({
        model: Static,
        parse: function(resp, options){
            console.log("statics parse");
            console.log(resp);
        },
        sync: function(method, model, options){
            if(method != "read"){
                console.error("Can only read from StaticSet");
                return;
            }
        }

    });

    /*
    _.each(statics, function(v, k){
        statics[k].Model = Static.extend({
            type: k,
            parameters: function(){
                return v.parameters;
            },
            commands: function(){
                return v.commands;
            }
        });
    });
    */



    var Musicazoo = Backbone.Model.extend({
        defaults: function(){
            return {
                queue: new Queue(),
                statics: new StaticSet(),
                active: new CurrentAction()
            };
        },
        fetch: function(){
            this.get('queue').fetch();
            this.get('statics').fetch();
            this.get('active').fetch();
        }
    });

    var QueueView = Backbone.View.extend({
        initialize: function(){
            this.listenTo(this.collection, "all", this.render); //FIXME?
            return this;
        },
        render:function(){
            this.$el.html(QUEUE_TEMPLATE(_.map(this.collection.models, function(m){
                return TEMPLATES[m.template_queue](m.attributes);
            })));
            return this;
        }
    });

    var ActiveView = Backbone.View.extend({
        initialize: function(){
            this.listenTo(this.model, "change", this.render);
            return this;
        },
        render: function(){
            this.$el.html(TEMPLATES[this.model.template_active](this.model.attributes));
            console.log("render active");
            console.log(TEMPLATES[this.model.template_active](this.model.attributes));
            return this;
        }
    });

    var StaticVolumeView = Backbone.View.extend({
        initialize: function(){
            this.listenTo(this.collection, "all", this.render);
        },
        _loaded: false,
        render: function(){
            if(this.collection.get("volume")){
                if(!this._loaded){
                    loadSlider();
                    this._loaded = true;
                }
                updateSlider(this.collection.get("volume").get('vol'));
            }
        }
    });

    mz = new Musicazoo();
    qv = new QueueView({collection: mz.get('queue'), el: $("ol.playlist")});
    cv = new ActiveView({model: mz.get('active'), el: $("ol.current")});
    vol = new StaticVolumeView({collection: mz.get('statics')});
    mz.fetch();


    var refreshPlaylist = function(firstTime){
        //vm.reload();
    }

    refreshPlaylist(true);
    // Refresh playlist every 1 seconds
    setInterval(refreshPlaylist, 1000);
});
