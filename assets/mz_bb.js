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


// Handlebars templates

var TEMPLATE_NAMES = {
};

var TEMPLATES = _.objectMap({
    "unknown": '(Unknown)',
    "empty": '',
    "nothing": '(Nothing)',
}, Handlebars.compile);

_.each(["youtube", "text", "netvid"], function(n){
    TEMPLATES[n] = Handlebars.compile($("script." + n + "-template").html());
    TEMPLATES[n + "_active"] = Handlebars.compile($("script." + n + "-active-template").html());
    TEMPLATE_NAMES[n] = {queue: n, active: n + "_active"};
});

_.each(["image", "logo"], function(n){
    //TEMPLATES[n] = Handlebars.compile($("script." + n + "-template").html());
    TEMPLATES[n] = Handlebars.compile($("script." + n + "-template").html());
    TEMPLATE_NAMES[n] = {queue: n, active: n };
});


// NLP Constants

var COMMANDS = [
    { // Text
        keywords: ["text", "say"],
        module: "text",
        args: function(match, cb, kw){
            cb({
                text: match,
                text_preprocessor: "none",
                speech_preprocessor: "pronunciation",
                text2speech: "google",
                renderer: "splash",
                duration: 1,
                short_description: "(Text)",
                long_description: "Text: " + match,
            });
        }
    },
    { // Tell me a joke
        module: "text",
        regex: /tell me a joke/,
        args: function(match, cb, kw){
            cb({
                text: "no",
                text_preprocessor: "none",
                speech_preprocessor: "none",
                text2speech: "google",
                renderer: "splash",
                duration: 1,
                short_description: "(Tell me a joke)",
                long_description: "Joke",
            });
        }
    },
    { // Luke I am your father
        module: "text",
        regex: /luke I am your father/i,
        args: function(match, cb, kw){
            cb({
                text: "no",
                text_preprocessor: "none",
                speech_preprocessor: "none",
                text2speech: "google",
                renderer: "splash",
                duration: 1,
                speed: 0.3,
                short_description: "(Awkward)",
                long_description: "Luke,",
            });
        }
    },
    { // Fuck
        module: "text",
        keywords: ["fuck"],
        args: function(match, cb, kw){
            var words = "ahole,aholes,asshole,assholes,asswipe,biatch,bitch,bitches,blo_job,blow_job,blowjob,cocksucker,cunt,cunts,dickhead,fuck,fucked,fucking,fuckoff,fucks,handjob,handjobs,motherfucker,mother-fucker,motherfuckers,muthafucker,muthafuckers,nigga,niggs,nigger,niggers,pedofile,pedophile,phag,phuc,phuck,phucked,phucker,shat,shit,shits,shithead,shitter,shitting".split(",");
            cb({
                text: _.chain(words).shuffle().last(10).value().join(" "),
                text_preprocessor: "none",
                speech_preprocessor: "none",
                text2speech: "google",
                renderer: "splash",
                duration: 2,
                speed: 1,
                short_description: "Fuck!",
                long_description: "(Please hold while Musicazoo expresses itself)",
            });
        }
    },
    { // Network video
        keywords: ["netvid"],
        module: "netvid",
        args: function(match, cb){
            cb({url: match, short_description: 'Network Video', long_description: match});
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
    { // Images
        keywords: ["image"],
        regex: /http.*(gif|jpe?g|png|bmp)/, 
        module: "image",
        background: true,
        args: function(match, cb){
            cb({image: match});
        }
    },
    { // Images
        keywords: ["logo"],
        module: "logo",
        background: true,
        args: function(match, cb){
            cb({});
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
    _query_queue.push({"data": data, "cb": cb, "err": err});
}

function forceQuery(data, cb, err){
    deferQuery(data, cb, err);
    runQueries();
}

function runQueries(cb, err){
    window.clearTimeout(_runquery_timeout);
    if(_query_queue.length){
        var cbs = _.pluck(_query_queue, "cb");
        var errs = _.pluck(_query_queue, "cb");
        var datas = _.pluck(_query_queue, "data");
        $.ajax(BASE_URL, {
            data: JSON.stringify(datas),
            dataType: 'json',
            type: 'POST',
            success: function(resp){
                regainConnection();
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
                _runquery_timeout = window.setTimeout(runQueries, 0); // Defer
            },
            error: function(){
                lostConnection();
                _.each(errs, function(x){ if(x){ x(); } });
                _runquery_timeout = window.setTimeout(runQueries, 500); // Connection dropped?
                if(err){
                    err();
                }
            }
        });
    }else{
        _runquery_timeout = window.setTimeout(runQueries, 50);
    }
    _query_queue = [];
}

function regainConnection(){
    $(".disconnect-hide").show();
    $(".disconnect-show").hide();
}

function lostConnection(){
    console.log("Lost connection");
    $(".disconnect-show").show();
    $(".disconnect-hide").hide();
}

function authenticate(cb){
    var doAuth = function(){
        // Auth & get capabilities
        console.log("trying to auth");
        var caps = {};
        deferQuery({cmd: "module_capabilities"}, function(mcap){
            caps.modules = mcap;
        });
        deferQuery({cmd: "static_capabilities"}, function(scap){
            caps.statics = scap;
        });
        deferQuery({cmd: "background_capabilities"}, function(bcap){
            caps.backgrounds = bcap;
        });
        runQueries(function(){
            cb(caps);
        }, function(){
            console.log("unable to auth");
            window.setTimeout(doAuth, 2000);
        });
    };
    doAuth();
}

var command_match = function(commands, text, cb){
    text = _.trim(text);
    var kw = _.strLeft(text, " ");
    var rest = _.strRight(text, " ");
    var match = null;
    for(var i = 0; i < commands.length; i++){
        var cmd = commands[i];
        var add_cmd = cmd.background ? 'set_bg' : 'add';
        if(cmd.keywords){
            if(_.contains(cmd.keywords, kw)){
                match = rest;
            }
        }
        if(cmd.regex){
            var regx = cmd.regex.exec(text);
            if(regx){
                match = regx[0];
            }
        }
        if(match){
            cmd.args(match, function(args){
                cb({cmd: add_cmd, args: {type: cmd.module, args: args}});
            }, kw);
            return true;
        }
    }
    return false;
}

var refreshPlaylist = function(){}; // Don't do anything, until we connect to the backend

$(document).ready(function(){
    $("#queueform").submit(function(e){
        e.preventDefault();
        var query = $(".addtxt").val();
        $(".addtxt").val("");
        if(!query){
            return false;
        }
        command_match(COMMANDS, query, function(args){
            deferQuery(args, refreshPlaylist, lostConnection);
            refreshPlaylist();
        });
        return false; // Prevent form submitting
    });

    $("#uploadform").submit(function(e){
        var $this = $("#uploadform");
        e.preventDefault();
        var formData = new FormData($this[0]);
        // Clear out the old file by replacing the DOM element.
        // Super hacky, but works cross-browser
        var fparent = $('input.uploadfile').parent();
        fparent.html(fparent.html());
        $this.hide();
        var $progbar = $('div.upload-progress-bar')
        $progbar.css('width', '3%');

        $.ajax({
            url: $this.attr('action'),  //server script to process data
            type: 'POST',
            xhr: function() {  // custom xhr
                var myXhr = $.ajaxSettings.xhr();
                if(myXhr.upload){ // check if upload property exists
                    myXhr.upload.addEventListener('progress',function(pe){
                            if(pe.lengthComputable){
                                var progress = (pe.loaded / pe.total);
                                $progbar.parent().show();
                                $progbar.animate({width: $progbar.parent().width() * progress + 'px'});
                            };
                        }, false); // for handling the progress of the upload
                }
                return myXhr;
            },
            //Ajax events
            //beforeSend: beforeSendHandler,
            success: function(){
                refreshPlaylist();
                $('div.upload-progress').hide();
                $this.show();
            },
            error: function(){
                lostConnection();
                $('div.upload-progress').hide();
                $this.show();
            },
            // Form data
            data: formData,
            //Options to tell JQuery not to process data or worry about content-type
            cache: false,
            contentType: false,
            processData: false
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
        var query = $(this).val();
        var $results = $(".results");
        if(query == ""){
            $results.html("");
            return;
        }
        var ytrequrl = "http://gdata.youtube.com/feeds/api/videos?v=2&orderby=relevance&alt=jsonc&q=" + encodeURIComponent(query) + "&max-results=5&callback=?"
        $.getJSON(ytrequrl, function(data){
            if(!$(".addtxt").val()){
                // If all the text from query box has been deleted, hide this box
                $results.html("");
                return;
            }
            var list = $("<ol class='suggest suggestions'></ol>");
            var tmpl = Handlebars.compile("<a class='push' href='#' content='http://youtube.com/watch?v={{{ id }}}'><li>{{ title }} - [{{ minutes duration }}] </li></a>");

            if(!data.data.items){
                $results.html("");
                return;
            }

            for(var j = 0; j < data.data.items.length && j < 5; j++){
                var vid = data.data.items[j];
                list.append($(tmpl(vid)));
            }
            $results.html("").append(list);
        });
        return true;
    });

});

var authCallback = _.once(function(capabilities){
    var modules = _.objectMap(capabilities.modules.specifics, function(x){ 
        x.commands = x.commands.concat(capabilities.modules.commands); 
        x.parameters = x.parameters.concat(capabilities.modules.parameters); 
        x.background = false;
        return x;
    });
    var backgrounds = _.objectMap(capabilities.backgrounds.specifics, function(x){ 
        x.commands = x.commands.concat(capabilities.backgrounds.commands); 
        x.parameters = x.parameters.concat(capabilities.backgrounds.parameters); 
        x.background = true;
        return x;
    });
    var statics = capabilities.statics;
    var module_capabilities = _.objectMap(modules, function(x){ return x.parameters });
    var background_capabilities = _.objectMap(backgrounds, function(x){ return x.parameters });
    var static_capabilities = _.objectMap(statics, function(x){ return x.parameters });
    var commands = _.filter(COMMANDS, function(x){ return  _.contains(_.keys(modules), x.module); });
    _.extend(modules, backgrounds);
    console.log("Modules:", modules);
    console.log("Statics:", statics);
    console.log("Commands:", commands);
    console.log("Module capabilities: ", module_capabilities);
    console.log("Static capabilities: ", static_capabilities);
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
                if(this.background){
                    this.template_queue = "empty";
                    this.template_active = "empty";
                }else{
                    this.template_queue = "empty";
                    this.template_active = "nothing";
                }
            }

            if(modules[type]){
                this.parameters = modules[type].parameters;
                this.commands = modules[type].commands;
                if(this.background != modules[type].background){
                    console.log("Background object on queue?", this);    
                }
            }else{
                this.parameters = [];
                this.commands = [];
            }

            // Send status updates to server
            this.off("change:status"); // Reset events
            if(this.hasParameter("status")){
                this.on("change:status", function(model, status, options){
                    if(!options.parse){ // Not a server update
                        var prev_status = this.previous('status');

                        // Play/pause switch
                        if(this.hasCommand("pause") && this.hasCommand("resume")){
                            if(prev_status == "paused" && status == "playing"){
                                deferQuery({cmd: "tell_module", args: {uid: this.id, cmd: "resume"}});
                            }else if(prev_status == "playing" && status == "paused"){
                                deferQuery({cmd: "tell_module", args: {uid:this.id, cmd: "pause"}});
                            }
                        }

                        // Stop
                        if(this.hasCommand("stop")){
                            if(status == "stopped"){
                                deferQuery({cmd: "tell_module", args: {uid:this.id, cmd: "stop"}});
                            }
                        }
                    }
                }, this);
            }

            // Seek
            this.off("change:time"); // Reset events
            if(this.hasParameter("time") && this.hasCommand("seek_abs")){
                this.on("change:time", function(model, time, options){
                    if(!options.parse){ // Not a server update
                        var prev_time = this.previous('time');
                        deferQuery({cmd: "tell_module", args: {uid: this.id, cmd: "seek_abs", args: {position: time}}});
                    }
                }, this);
            }
        },
        initialize: function(params, options, x){
            this.on("change:type", this.updateType, this);
            this.on("change:exists", this.updateType, this);
            this.updateType();
        },
        sync: function(method, model, options){
            if(method == "read"){
                if(this.background){
                    deferQuery({cmd: "bg", args: {parameters: background_capabilities}}, options.success, options.error);
                }else if(this.active){
                    deferQuery({cmd: "cur", args: {parameters: module_capabilities}}, options.success, options.error);
                }else{
                    console.error("Unable to sync queue item");
                }
            }else if(method == "delete"){
                console.log("deleting", model)
                if(this.background){
                    //TODO - You can't actually delete backgrounds
                    console.error("How do I delete a background!?");
                    deferQuery({cmd: "rm", args: {uids: [model.id]}}, options.success, options.error);
                }else if(this.active){
                    //deferQuery
                    // Eh, try anyways
                    deferQuery({cmd: "rm", args: {uids: [model.id]}}, options.success, options.error);
                    //deferQuery({cmd: "tell_module", args: {uid: model.id, cmd: "stop"}});
                }else{
                    deferQuery({cmd: "rm", args: {uids: [model.id]}}, options.success, options.error);
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
        active: false,
        background: false
    });

    var CurrentAction = Action.extend({
        active: true
    });

    var Background = CurrentAction.extend({
        background: true
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
            deferQuery({cmd: "queue", args: {parameters: module_capabilities}}, options.success, options.error);
        }
    });

    var Static = Backbone.Model.extend({
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
            deferQuery({cmd: "statics", args: {parameters: static_capabilities}}, options.success, options.error);
        }

    });

    var Musicazoo = Backbone.Model.extend({
        defaults: function(){
            return {
                queue: new Queue(),
                statics: new StaticSet(),
                active: new CurrentAction(),
                background: new Background(),
            };
        },
        fetch: function(){
            this.get('queue').fetch();
            this.get('statics').fetch();
            this.get('active').fetch();
            this.get('background').fetch();
        }
    });

    var ActionView = Backbone.View.extend({
        act_template: Handlebars.compile("<a href='#' class='btn rm de-only'></a>{{{ html }}}<a href='#' class='btn rm bb-only'>rm</a>"),
        events: {
            "click .rm": "remove",
            "click .cmd": "cmd",
            "click .action-set": "actionSet",
            "click .video-progress": "setProgress",
            "click .video-progress-bar": "setProgress",
            "click .youtube-add-related": "addRelatedYoutube",
        },
        initialize: function(){
            var self = this;
            this.listenTo(this.model, "change", this.render);
            this.listenTo(this.model, "change:vid", function(){ self.model.unset("related"); } );
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
            this.model.destroy();
        },
        actionSet : function(ev){
            var $t = $(ev.target);
            var property = $t.attr('data-property');
            var value = $t.attr('data-value');
            var old_val = this.model.get(property);
            if(_.isNumber(old_val)){
                value = parseFloat(value);
            }
            this.model.set(property, value);
        },
        setProgress: function(ev){
            var seekTo = Math.floor(ev.offsetX / this.$(".video-progress").width() * this.model.get("duration"));
            console.log("seek to:", seekTo, this.model.get("duration"));
            this.$(".video-progress-bar").css("width", ev.offsetX + "px");
            this.model.set("time", seekTo);
        },
        addRelatedYoutube: function(ev){
            var self = this;
            var pushVideo = function(){
                var related = self.model.get('related');
                var rel = related.pop();
                deferQuery({cmd: 'add', args: {type: 'youtube', args: {url: rel.url}}});
                refreshPlaylist();
            };
            var vid = this.model.get('vid');
            var related_url = "https://gdata.youtube.com/feeds/api/videos/" + vid + "/related?v=2&alt=json&callback=?";
            if(this.model.has('related')){
                pushVideo();
                return;
            }
            $.getJSON(related_url, function(data){
                // Did we manage to pull the related feed while waiting for this callback?
                if(self.model.has('related')){
                    pushVideo();
                    return;
                }
                var raw_entries = data.feed.entry;
                var entries = _.map(raw_entries, function(e){
                    return {'title': e.title.$t, 'url': e.link[0].href};
                });
                self.model.set('related', entries);
                pushVideo();
            });
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
    var BackgroundView = ActiveView.extend({
    });

    var QueueView = Backbone.View.extend({
        initialize: function(){
            var self = this;
            this.subviews = {};
            this.no_autorefresh = false;
            this.$el.sortable({
                update: function(ev, ui){
                    var ordering = self.$("li").map(function(i, e){return $(e).attr('data-view-id')}).toArray();
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

            $("a.clear").click(function(){
                self.collection.each(function(m){ m.destroy(); });
            });

            this.listenTo(this.collection, "add", this.addOne);
            this.listenTo(this.collection, "remove", this.removeOne); 
            this.listenTo(this.collection, "all", this.render); //FIXME?
            return this;
        },
        addOne: function(model){
            var $v_el = $("<li class='entry'></li>").attr("data-view-id", model.id);
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
            if(event != "reset" && event != "sync"){
                self.$el.html($(_.map(this.collection.models, function(model){
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
            this.render();
            this.listenTo(this.model, "change:vol", this.render);
        },
        loadSlider : _.once(function(){
            var self = this;
            var setVal = _.debounce(function(x){
                self.model.set('vol', x);
            }, 500);
            if(!DE){
                $("div.vol-slider").slider({
                    orientation: "horizontal",
                    range: "min",
                    min: 0,
                    max: 100,
                    value: window.volume,
                    slide: function(ev, ui) {
                        self.updateSlider(ui.value);
                        setVal(ui.value); // debounced
                    }
                });
            }else{
                $("div.volume").slider({ //TODO: Why doesn't this update?
                    orientation: "horizontal",
                    range: "min",
                    min: 0,
                    max: 100,
                    value: window.volume,
                    slide: function(ev, ui) {
                        self.updateSlider(ui.value);
                        setVal(ui.value); // debounced
                    }
                });
            }
        }),
        updateSlider : function(value){
            $("div.vol-slider").slider("option", "value", value);
            if(!DE){
                $(".ui-slider-range").html("<span>" + value + "</span>");
            }
        },
        render: function(v){
            //var vol = this.collection.findWhere({"class": "volume"});
            this.loadSlider();
            this.updateSlider(this.model.get('vol'));
        },
    });

    var StaticIdentityView = Backbone.View.extend({
        initialize: function(){
            this.render();
        },
        render: function(v){
            $("h1.title").text(this.model.get("name"));
            $("html").css("background", this.model.get("colors")['bg']);
        }
    });

    var StaticSetView = Backbone.View.extend({
        initialize: function(){
            this.listenTo(this.collection, "add", function(model){
                if(model.get('class') == "volume"){
                    var sv = new StaticVolumeView({model: model});
                }else if(model.get('class') == "identity"){
                    var sv = new StaticIdentityView({model: model});
                }
            });
        }
    });

    mz = new Musicazoo();
    var qv = new QueueView({collection: mz.get('queue'), el: $("ol.playlist")});
    var cv = new ActiveView({model: mz.get('active'), el: $("ol.current")});
    var bv = new BackgroundView({model: mz.get('background'), el: $("ol.background")});
    var ssv = new StaticSetView({collection: mz.get('statics')});
    mz.fetch();

    refreshPlaylist = function(){
        mz.fetch();
    }

    refreshPlaylist();
    // Refresh playlist every 1 seconds
    setInterval(refreshPlaylist, 1000);
});

authenticate(authCallback);
