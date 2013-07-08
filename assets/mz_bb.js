// Youtube iframe

/*
var player;
function playYoutubeVideo(id, time) {
    player = new YT.Player('video', {
        height: '390',
        width: '640',
        //videoId: id,
        events: {
            'onReady': function(ev){
                //ev.target.playVideo(); 
                player.loadVideoById(id, time);
                //ev.target.seekTo(time*1, true);
            },
            'onStateChange': function(ev){
                console.log(ev);
            }
        }
    });
    console.log(player);
}
*/

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


// Handlebars templates

var TEMPLATE_NAMES = {
    "youtube": {
        queue: "youtube",
        active: "youtube_active"
    },
    "text": {
        queue: "text",
        active: "text_active"
    }
};

var TEMPLATES = _.chain({
    /*
    "youtube": '<a href="{{ url }}">{{ title }}</a> - [{{ minutes duration }}] -  ({{ status}}:{{site }})',
    "youtube_active": '<div id="youtube-video"></div>' + 
                      '<a href="{{ url }}">{{ title }}</a> - [{{ minutes time }}/{{ minutes duration }}] - ({{ status}}:{{site }})' +
                      '{{#ifPlaying status }}&nbsp;<a href="#" class="action-set" data-property="status" data-value="paused">pause</a>{{/ifPlaying}}' +
                      '{{#ifPaused status }}&nbsp;<a href="#" class="action-set" data-property="status" data-value="playing">resume</a>{{/ifPaused}}' +
                      '&nbsp;<a href="#" class="action-set" data-property="status" data-value="stopped">stop</a>',
    */
    "youtube": $("script.youtube-template").html(),
    "youtube_active": $("script.youtube-active-template").html(),
    "text": $("script.text-active-template").html(),
    "text_active": $("script.text-template").html(),
    "unknown": '(Unknown)',
    "empty": '',
    "nothing": '(Nothing)',
}).map(function(v, k){  return [k, Handlebars.compile(v)] }).object().value();

// NLP Constants

var COMMANDS = [
    { // Text
        keywords: ["text", "say"],
        module: "text",
        args: function(match, cb, kw){
            cb({
                text: match,
                text_preprocessor: "none",
                speech_preprocessor: "none",
                text2speech: "google",
                renderer: "splash",
                duration: 1
            });
        }
    },
    { // Youtube
        keywords: ["youtube"],
        regex: /.*youtube.com.*watch.*v.*/, 
        module: "youtube",
        args: function(match, cb){
            cb({url: match});
        }
    },
    // Playlist
    // https://gdata.youtube.com/feeds/api/playlists/4DAEFAF23BB3CDD0?alt=jsonc&v=2
    { // Youtube (Keyword search)
        regex: /.*/, 
        module: "youtube",
        args: function(match, cb){
            var ytrequrl = "http://gdata.youtube.com/feeds/api/videos?v=2&orderby=relevance&alt=jsonc&q=" + encodeURIComponent(match) + "&max-results=5&callback=?"
            $.getJSON(ytrequrl, function(data){
                if(data.data.items.length >= 1){
                    cb({url: "http://youtube.com/watch?v=" + data.data.items[0].id});
                }
            });
        }
    }
];


var volume_lockout = false;
setInterval(function(){ volume_lockout = false; }, 500);


var _query_queue = [];
var _runquery_timeout;
//var BASE_URL = "http://localhost:9000/";
var BASE_URL = "/cmd";

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

var command_match = function(commands, text, cb){
    text = _.trim(text);
    var kw = _.strLeft(text, " ");
    var rest = _.strRight(text, " ");
    var match = null;
    for(var i = 0; i < commands.length; i++){
        var cmd = commands[i];
        if(cmd.keywords){
            if(_.contains(cmd.keywords, kw)){
                match = rest;
            }
        }
        if(cmd.regex){
            var regx = cmd.regex.exec(text);
            console.log(regx);
            if(regx){
                match = regx[0];
            }
        }
        if(match){
            cmd.args(match, function(args){
                cb({type: cmd.module, args: args});
            }, kw);
            return true;
        }
    }
    return false;
}


$(document).ready(function(){
    $("#queueform").submit(function(e){
        e.preventDefault();
        console.log("queue");
        var query = $(".addtxt").val();
        if(!query){
            return false;
        }
        $(".addtxt").val("");
        command_match(COMMANDS, query, function(args){
            deferQuery({cmd: "add", args: args}, refreshPlaylist);
        });
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
            var tmpl = Handlebars.compile("<a class='push' href='#' content='http://youtube.com/watch?v={{{ id }}}'><li>{{ title }} - [{{ minutes duration }}] </li></a>");

            for(var j = 0; j < data.data.items.length && j < 5; j++){
                var vid = data.data.items[j];
                //console.log(vid);
                //list.append($("<a class='push' href='#' content='http://youtube.com/watch?v=" + vid.id + "'><li>" + vid.title + "</li></a>"));
                list.append($(tmpl(vid)));
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

    */
    

});

var loadSlider = function(updateCb){
    var debouncedCb = _.debounce(updateCb, 300);
    $("div.vol-slider").slider({
        orientation: "horizontal",
        range: "min",
        min: 0,
        max: 100,
        value: window.volume,
        slide: function(ev, ui) {
            updateSlider(ui.value);
            debouncedCb(ui.value);
        }
    });
    updateSlider(window.volume);
}

var updateSlider = function(value){
    $("div.vol-slider").slider("option", "value", value);
    $(".ui-slider-range").html("<span>" + value + "</span>");
}




authenticate(function(capabilities){
    var modules = _.objectMap(capabilities.modules.specifics, function(x){ 
        x.commands = x.commands.concat(capabilities.modules.commands); 
        x.parameters = x.parameters.concat(capabilities.modules.parameters); 
        return x;
    });
    var statics = capabilities.statics;
    var static_capabilities = _.objectMap(statics, function(x){ return x.parameters });
    var module_capabilities = _.objectMap(modules, function(x){ return x.parameters });
    var commands = _.filter(COMMANDS, function(x){ return  _.contains(_.keys(modules), x.module); });
    console.log("Modules:", modules);
    console.log("Statics:", statics);
    console.log("Commands:", commands);
    console.log(capabilities);
    console.log(module_capabilities);
    console.log(static_capabilities);
    Backbone.sync = function(method, model, options){
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
        updateType: function(){
            var type = this.get('type')
            if(this.get('exists')){
                if(TEMPLATES[type]){
                    this.template_queue = TEMPLATE_NAMES[type].queue;
                    this.template_active = TEMPLATE_NAMES[type].active;
                }else{
                    this.template_queue = "unknown";
                    this.template_active = "unknown";
                }
            }else{
                this.template_queue = "empty";
                this.template_active = "nothing";
            }

            if(modules[type]){
                this.parameters = modules[type].parameters;
                this.commands = modules[type].commands;
            }else{
                this.parameters = [];
                this.commands = [];
            }

            if(this.hasCommand("pause") && this.hasCommand("resume") && this.hasParameter("status")){
                //console.log("Registering status");
                this.on("change:status", function(model, status, options){
                    if(!options.parse){ // Not a server update
                        var prev_status = this.previous('status');
                        if(prev_status == "paused" && status == "playing"){
                            deferQuery({cmd: "tell_module", args: {uid: this.id, cmd: "resume"}});
                        }else if(prev_status == "playing" && status == "paused"){
                            deferQuery({cmd: "tell_module", args: {uid:this.id, cmd: "pause"}});
                        }else if(status == "stopped"){
                            deferQuery({cmd: "tell_module", args: {uid:this.id, cmd: "stop"}});
                        }
                    }
                }, this);
            }else{
                this.off("change:status");
            }
        },
        initialize: function(params, options, x){
            this.on("change:type", this.updateType, this);
            this.on("change:exists", this.updateType, this);
            this.updateType();
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
                    //deferQuery({cmd: "tell_module", args: {uid: model.id, cmd: "stop"}});
                }else{
                    deferQuery({cmd: "rm", args: {uids: [model.id]}}, options.success);
                }
            }else{
                console.log("ERROR:", "Unable to perform action on queue item:" + method);
            }
            return this;
        },
        parse: function(resp, options){
            if(resp){
                var attrs = {type: resp.type, uid: resp.uid, _order: resp._order, exists: true};
                _.each(resp.parameters, function(v, k){ attrs[k] = v; });
                return attrs;
            }else{
                return {'exists': false};
            }
        },
        idAttribute: "uid",
        hasParameter: function(p){ return _.contains(this.parameters, p); },
        hasCommand: function(p){ return _.contains(this.commands, p); },
        template_queue: "unknown",
        template_active: "unknown",
        active: false
    });

    var CurrentAction = Action.extend({
        active: true
    });

    var Queue = Backbone.Collection.extend({
        model: Action,
        comparator: "_order",
        parse: function(resp, options){
            return _.map(resp, function(r, i){ r._order = i; return r});
        },
        sync: function(method, model, options){
            if(method != "read"){
                console.error("Can only read from Queue");
                return;
            }
            deferQuery({cmd: "queue", args: {parameters: module_capabilities}}, options.success);
        }
    });
    
    var Static = Backbone.Model.extend({
        defaults: function(){
            return {

            };
        },
        initialize: function(prop, options){
            this.parameters = statics[prop.uid].parameters;
            this.commands = statics[prop.uid].commands;
            if(this.hasParameter('vol') && this.hasCommand('set_vol')){
                this.on('change:vol', function(model, vol, options){
                    if(!options.parse){
                        deferQuery({cmd: "tell_static", args: {"uid": this.id, "cmd": "set_vol", "args": {"vol": vol}}});
                    }
                });
            }
        },
        idAttribute: "uid",
        hasParameter: function(p){ return _.contains(this.parameters, p); },
        hasCommand: function(p){ return _.contains(this.commands, p); }
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
        events: {
            "click .rm": "remove",
            "click .cmd": "cmd",
            "click .action-set": "actionSet",
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
        },
        actionSet : function(ev){
            var $t = $(ev.target);
            var property = $t.attr('data-property');
            var value = $t.attr('data-value');
            this.model.set(property, value);
        },
        cmd: function(ev){
            var action = $(ev.target).attr("data-action");
            console.log("DEPRICATED 'cmd'");
            deferQuery({cmd: "tell_module", args: {uid: this.model.id, cmd: action}});
        },
    });
    var ActiveView = ActionView.extend({
        act_template: Handlebars.compile("{{{ html }}}"),
        initialize: function(){
            this.listenTo(this.model, "change", this.render);
            this.listenTo(this.model, "change:uid", function(model){
                //playYoutubeVideo(model.get('vid'), model.get('time'));
            });
            this.render();
            return this;
        }
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

            }else if(event == "sync"){
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
            this.listenTo(this.collection, "add", this.render);
            this.listenTo(this.collection, "change:vol", this.updateVolSlide);
        },
        _loaded: false,
        render: function(act){
            var vol = this.collection.findWhere({"class": "volume"}); 
            if(vol){
                if(!this._loaded){ //FIXME?
                    loadSlider(function(val){
                        vol.set('vol', val);    
                    });
                    this._loaded = true;
                }
            }
        },
        updateVolSlide: function(model, v){
            updateSlider(v);
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
