// Underscore mixins
_.mixin(_.str.exports());

_.mixin({
    objectMap : function(obj, fn){
        return _.chain(obj).map(function(v, k){ return [k, fn(v)] }).object().value();
    }
});


// Handlebars extras
Handlebars.registerHelper('minutes', function(seconds){
    var output = "";
    if(seconds > 3600){
        var hours = Math.floor(seconds / 3600);
        output = hours + ":";
        seconds %= 3600;
    }
    var minutes = Math.floor(seconds / 60);
    seconds %= 60;
    seconds = Math.floor(seconds);
    output += minutes + ":" + seconds;
    return output
});

// NLP Constants

var COMMANDS = [
    {
        keywords: ["youtube"],
        regex: /.*youtube.com.*watch.*v.*/, 
        module: "youtube",
        args: function(match){
            return match;
        }
    },
    {
        regex: /.*/, 
        module: "youtube",
        args: function(match){
            //TODO: lookup video
            console.error("Need to query for video");
            return match;
        }
    }
];


var volume_lockout = false;
setInterval(function(){ volume_lockout = false; }, 500);


var _query_queue = [];
var _runquery_timeout;
//var BASE_URL = "http://localhost:9000/";
var BASE_URL = "/";

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
    var caps = {};
    deferQuery({cmd: "module_capabilities"}, function(mcap){
        caps.modules = mcap;
    });
    deferQuery({cmd: "static_capabilities"}, function(scap){
        caps.statics = scap;  
    });
    runQueries(function(){
        cb(caps);
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
    $("#queueform").submit(function(e){
        e.preventDefault();
        console.log("queue");
        var query = $(".addtxt").val();
        if(!query){
            return false;
        }
        $(".addtxt").val("");
        deferQuery({cmd: "add", args: {type: "youtube", args: {url: query}}}, refreshPlaylist);
        return false; // Prevent form submitting
    });

    $(".results").delegate("a.push", "click", function(){
        var $this = $(this);
        $(".addtxt").val($this.attr("content"));
        $(".results").html("");
        $("#queueform").submit();
    });

    $("input.addtxt").keyup(function(){
        console.log('asdf');
        var query = $(this).val();
        if(query == ""){
            $(".results").html("");
            return;
        }
        var ytrequrl = "http://gdata.youtube.com/feeds/api/videos?v=2&orderby=relevance&alt=jsonc&q=" + encodeURIComponent(query) + "&max-results=5&callback=?"
        $.getJSON(ytrequrl, function(data){
            var list = $("<ol class='suggest'></ol>");

            for(var j = 0; j < data.data.items.length && j < 5; j++){
                var vid = data.data.items[j];
                list.append($("<a class='push' href='#' content='http://youtube.com/watch?v=" + vid.id + "'><li>" + vid.title + "</li></a>"));
            }
            $(".results").html("").append(list);
        });
        return true;
    });

    
/*
    $(".uploadFile").submit(function(){
        $(".queueform");
    });

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
    

});

var loadSlider = function(updateCb){
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
            updateCb(ui.value, function(){
                volume_lockout = false;    
            });
        }
    });
    updateSlider(window.volume);
}

var updateSlider = function(value){
    $("div.vol-slider").slider("option", "value", value);
    $(".ui-slider-range").html("<span>" + value + "</span>");
}




var TEMPLATE_NAMES = {"youtube": {queue: "youtube", active: "youtube_active"} };
var TEMPLATES = _.chain({
    "youtube": '<a href="{{ url }}">{{ title }}</a> - [{{ minutes duration }}] -  ({{ status}}:{{site }})',
    "youtube_active": '<a href="{{ url }}">{{ title }}</a> - [{{ minutes duration }}] - ({{ status}}:{{site }})',
    "unknown": '(Unknown)',
    "unknown": '(Unknown)',
    "empty": '',
    "nothing": '(Nothing)',
}).map(function(v, k){ return [k, Handlebars.compile(v)] }).object().value();

var QUEUE_TEMPLATE = Handlebars.compile('{{#each this}}\n<li>{{{this}}}</li>{{/each}}');


authenticate(function(capabilities){
    var modules = _.objectMap(capabilities.modules.specifics, function(x){ 
        x.commands = x.commands.concat(capabilities.modules.commands); 
        x.parameters = x.parameters.concat(capabilities.modules.parameters); 
        return x;
    });
    console.log("Modules:", modules);
    var statics = capabilities.statics;
    console.log("Statics:", statics);
    //var module_capabilities = _.chain(modules).map(function(v, k){ return [k, v.parameters] }).object().value();
    var static_capabilities = _.objectMap(statics, function(x){ return x.parameters });
    var module_capabilities = _.objectMap(modules, function(x){ return x.parameters });
    console.log(capabilities);
    console.log(module_capabilities);
    console.log(static_capabilities);
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
                exists: true,
            };
        },
        sync: function(method, model, options){
            if(method == "read"){
                if(this.active){
                    deferQuery({cmd: "cur", args: {parameters: module_capabilities}}, options.success);
                }else{
                    console.error("Unable to sync queue item");
                }
            }else if(method == "delete"){
                console.log("deleting", model)
                if(this.active){
                    //deferQuery
                    // Eh, try anyways
                    deferQuery({cmd: "rm", args: {uids: [model.id]}}, options.success);
                    deferQuery({cmd: "tell_module", args: {uid: model.id, cmd: "stop"}});
                }else{
                    deferQuery({cmd: "rm", args: {uids: [model.id]}}, options.success);
                }
            } else{
                console.error("Unable to perform action on queue item:" + method);
            }
            return this;
        },
        parse: function(resp, options){
            if(resp){
                var attrs = {type: resp.type, uid: resp.uid, exists: true};
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
            }else{
                this.template_queue = "empty";
                this.template_active = "nothing";
                return {'exists': false};
            }
        },
        idAttribute: "uid",
        parameters: [],
        commands: [],
        template_queue: "unknown",
        template_active: "unknown",
        active: false
    });

    var CurrentAction = Action.extend({
        active: true
    });

    var Queue = Backbone.Collection.extend({
        model: Action,
        parse: function(resp, options){
            return resp;
        },
        sync: function(method, model, options){
            if(method != "read"){
                console.error("Can only read from Queue");
                return;
            }
            deferQuery({cmd: "queue", args: {parameters: module_capabilities}}, options.success);
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
            if(resp){
                //var attrs = {class: resp.class, uid: resp.uid, exists: true};
                var attrs = {};
                _.each(resp, function(v, k){ attrs[k] = v; });
                //console.log('static', attrs, resp);

                this.parameters = statics[resp.uid].parameters;
                this.commands = statics[resp.uid].commands;
                return attrs;
            }else{
                return {};
            }
        },
        idAttribute: "uid",
        parameters: [],
        commands: []
    });
    
    var StaticSet = Backbone.Collection.extend({
        model: Static,
        parse: function(resp, options){
            //console.log("statics parse");
            //console.log(resp);
            // Flatten dict to list
            return _.map(resp, function(v, k){ 
                v.uid = k;
                v.class = statics[k].class;
                return v;
             });
        },
        sync: function(method, model, options){
            if(method != "read"){
                console.error("Can only read from StaticSet");
                return;
            }
            deferQuery({cmd: "statics", args: {parameters: static_capabilities}}, options.success);
        }

    });

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

    var ActionView = Backbone.View.extend({
        act_template: Handlebars.compile("{{{ html }}} <a href='#' class='rm'>rm</a>"),
        tagName: "li",
        events: {
            "click .rm": "remove",
        },
        initialize: function(){
            this.listenTo(this.model, "change", this.render);
            this.render();
            return this;
        },
        render: function(ev){
            var tmpl = this.model.active ? "template_active" : "template_queue";
            this.$el.html(this.act_template({
                html: TEMPLATES[this.model[tmpl]](this.model.attributes),
                model: this.model
            }));
            return this;

        },
        remove: function(){
            console.log("Remove!", this.model);
            this.model.destroy();
        }

    });
    var ActiveView = ActionView.extend({
        act_template: Handlebars.compile("{{{ html }}} <a href='#' class='rm'>stop</a>"),
    });

    var QueueView = Backbone.View.extend({
        initialize: function(){
            this.subviews = {};
            this.no_autorefresh = false;
            this.$el.sortable({
                update: function(ev, ui){
                    var ordering = $("ol.playlist li").map(function(i, e){return $(e).attr('data-view-id')}).toArray();
                    console.log("ORDERING:", ordering);
                    // idk where this could go
                    deferQuery({cmd: "mv", args:{uids: ordering}});
                },
                start: function(ev, ui){
                    self.no_autorefresh = true;
                },
                stop: function(ev, ui){
                    self.no_autorefresh = false;
                },
            });

            this.listenTo(this.collection, "add", this.addOne);
            this.listenTo(this.collection, "remove", this.removeOne); 
            this.listenTo(this.collection, "all", this.render); //FIXME?
            return this;
        },
        addOne: function(model){
            var $v_el = $("<li></li>").attr("data-view-id", model.id);
            var view = new ActionView({model: model, el: $v_el});
            this.subviews[model.id] = view;
            this.render();
        },
        removeOne: function(model){
            this.subviews[model.id].$el.detach();
            delete this.subviews[model.id];
        },
        render: function(event, model, collection, options){
            if(this.no_autorefresh){
                return;
            }

            var self = this;
            if(event == "reset"){ 
                console.error("RESET QUEUEVIEW"); //???
                this.subviews = {}; // Clear
                _.each(this.collection.models, _.bind(this.addOne, this));

            }else{
                console.log("Queueview event", event);

                this.$el.html($(_.map(this.collection.models, function(model){
                    if(self.subviews[model.id]){ //TODO hack
                        return self.subviews[model.id].el;
                    }
                })));

                // Delegate events to models now added to the DOM
                _.each(this.subviews, function(view){
                    view.delegateEvents();
                });

            }
            return this;
        }
    });


    var StaticVolumeView = Backbone.View.extend({
        initialize: function(){
            this.listenTo(this.collection, "all", this.render);
        },
        _loaded: false,
        render: function(act){
            //console.log("static view", act, this.collection);
            var vol = this.collection.findWhere({"class": "volume"}); 
            if(vol){
                if(!this._loaded){ //FIXME?
                    loadSlider(function(val, cb){
                        vol.set('vol', val);    
                        deferQuery({cmd: "tell_static", args: {"uid": vol.id, "cmd": "set_vol", "args": {"vol": val}}}, cb);
                    });
                    this._loaded = true;
                }
                updateSlider(vol.get('vol'));
            }
        }
    });

    mz = new Musicazoo();
    qv = new QueueView({collection: mz.get('queue'), el: $("ol.playlist")});
    cv = new ActiveView({model: mz.get('active'), el: $("ol.current")});
    vol = new StaticVolumeView({collection: mz.get('statics')});
    mz.fetch();


    refreshPlaylist = function(firstTime){
        if(!window.no_autorefresh){
            mz.fetch();
        }
    }

    refreshPlaylist(true);
    // Refresh playlist every 1 seconds
    setInterval(refreshPlaylist, 1000);
});
