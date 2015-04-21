var MODULES = {
    "youtube": {
        commands: ["seek_abs", "seek_rel", "pause", "resume"],
        parameters: [
            "url", "title", "duration", "site", "media", "thumbnail", "description",
            "time", "status", "vid"
        ],
        background: false
    },
    "text": {
        commands: [],
        parameters: [
            "text", "duration", 
            "text2speech", "text2screen", "speech_preprocessor", "screen_preprocessor", "text2screen_args", "text2speech_args"
        ],
        background: false,
    },
    "problem": {
        commands: [],
        parameters: [],
        background: false,
    },
};

var BACKGROUNDS = {
    "text_bg": {
        commands: [],
        parameters: [
            "text", "duration", 
            "text2speech", "text2screen", "speech_preprocessor", "screen_preprocessor", "text2screen_args", "text2speech_args"
        ],
        background: true,
    },
    "image": {
        commands: [],
        parameters: ["url"],
        background: true,
    },
};

/* DEPRECATED 
var COMMANDS = [
    { // Text
        keywords: ["text", "say"],
        module: "text",
        args: function(match, cb, kw){
            cb({
                text: match,
                speech_preprocessor: "pronounce",
                text2speech: "google",
                text2screen: "splash",
                duration: 1,
            });
        }
    },
    { // Text
        keywords: ["remind", "splash"],
        module: "text_bg",
        background: true,
        args: function(match, cb, kw){
            cb({
                text: match,
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
                speech_preprocessor: "pronounce",
                text2speech: "google",
                text2screen: "paragraph",
                duration: 2,
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
    { // BTC
        keywords: ["btc"],
        module: "btc",
        args: function(match, cb){
            cb({});
        }
    },
    { // VBA - Play some pokemon
        keywords: ["vba", "pokemon"],
        module: "vba",
        args: function(match, cb){
            cb({});
        }
    },
    { // Images
        keywords: ["image"],
        regex: /http.*(gif|jpe?g|png|bmp)/, 
        module: "image",
        background: true,
        args: function(match, cb){
            cb({url: match});
        }
    },
    { // "Youtube"
        keywords: ["youtube", "video"],
        regex: /http.*.?/, 
        module: "youtube",
        args: function(match, cb){
            cb({url: match});
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
        regex: /.*.?/, 
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
*/

// Handlebars templates

var TEMPLATES = _.objectMap({
    "unknown": '(Unknown)',
    "empty": '',
    "nothing": '(Nothing)',
}, Handlebars.compile);

var TEMPLATES_TO_COMPILE = ["youtube", "text", "netvid", "btc", "vba", "image", "logo"];

_.each(TEMPLATES_TO_COMPILE, function(n){
    TEMPLATES[n] = Handlebars.compile($("script." + n + "-template").html());
});

function authenticate(cb){
    var doAuth = function(){
        // Auth & get capabilities
        console.log("trying to auth");
        var caps = {};
        queue_endpoint.deferQuery({cmd: "modules_available"}, function(mcap){
            caps.modules = mcap;
        });
        queue_endpoint.deferQuery({cmd: "backgrounds_available"}, function(bcap){
            caps.backgrounds = bcap;
        });
        queue_endpoint.runQueries(function(){
            cb(caps);
        }, function(){
            console.log("unable to auth");
            window.setTimeout(doAuth, 2000);
        });
    };
    doAuth();
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
        nlp_endpoint.deferQuery({"cmd": "do", "args": {"message": query}}, refreshPlaylist, lostConnection);
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

    var last_nlp_update = -1;
    $("input.addtxt").keyup(function(){
        var query = $(this).val();
        var $results = $(".results");
        if(query == ""){
            $results.html("");
            return;
        }
        var query_time = +(new Date());
        nlp_endpoint.deferQuery({"cmd": "suggest", "args": {"message": query}}, function(response){
            if(!$(".addtxt").val()){
                // If all the text from query box has been deleted, hide this box
                $results.html("");
                return;
            }

            // Handle results that are out of order
            if(last_nlp_update > query_time) return;
            last_update = query_time;

            var list = $("<ol class='suggest suggestions'></ol>");
            var tmpl = Handlebars.compile("<a class='push' href='#' content='{{ action }}'><li>{{ title }}</li></a>");

            if(!response.suggestions){
                $results.html("");
                return;
            }

            for(var j = 0; j < response.suggestions.length && j < 5; j++){
                var s = response.suggestions[j];
                list.append($(tmpl(s)));
            }
            $results.html("").append(list);
        });
        return true;
    });
});

// Backbone 
Backbone.sync = function(method, model, options){
    // Replace default sync function to raise error unless overridden
    console.error("unsupported sync");
    console.log(method, model, options);
}

var authCallback = _.once(function(available){
    console.log("available:", available);
    var modules = _(MODULES).pick(available.modules);
    var backgrounds = _(BACKGROUNDS).pick(available.backgrounds);

    var module_capabilities = _.objectMap(modules, function(x){ return x.parameters });
    var background_capabilities = _.objectMap(backgrounds, function(x){ return x.parameters });

    //var commands = _.filter(COMMANDS, function(x){ return  _.contains(_.keys(modules), x.module); });

    _.extend(modules, backgrounds);

    console.log("Modules:", modules);
    //console.log("Backgrounds:", backgrounds);

    // Action - module/item on queue. May or may not be running.
    var Action = Backbone.Model.extend({
        active: true, // everything is active! MZ5
        defaults: {
            type: null,
            exists: true,
        },
        updateType: function(){
            var type = this.get('type')
            if(this.get('exists')){
                if(TEMPLATES[type]){
                    this.template = type;
                }else{
                    this.template = "unknown";
                }
            }else{
                if(this.background){
                    this.template = "empty";
                }else{
                    this.template = "nothing";
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
                        console.log(this.hasCommand("pause"), this.commands);
                        if(this.hasCommand("pause") && this.hasCommand("resume")){
                            if(prev_status == "paused" && status == "playing"){
                                queue_endpoint.deferQuery({cmd: "tell_module", args: {uid: this.id, cmd: "resume"}});
                            }else if(prev_status == "playing" && status == "paused"){
                                queue_endpoint.deferQuery({cmd: "tell_module", args: {uid:this.id, cmd: "pause"}});
                            }
                        }

                        // Stop
                        if(this.hasCommand("stop")){
                            if(status == "stopped"){
                                queue_endpoint.deferQuery({cmd: "tell_module", args: {uid:this.id, cmd: "stop"}});
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
                        console.log("seek", time);
                        queue_endpoint.deferQuery({cmd: "tell_module", args: {uid: this.id, cmd: "seek_abs", args: {position: time}}});
                    }
                }, this);
            }

            // Rate
            this.off("change:rate"); // Reset events
            if(this.hasParameter("rate") && this.hasCommand("set_rate")){
                this.on("change:rate", function(model, rate, options){
                    if(!options.parse){ // Not a server update
                        queue_endpoint.deferQuery({cmd: "tell_module", args: {uid: this.id, cmd: "set_rate", args: {rate: rate}}});
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
                    queue_endpoint.deferQuery({cmd: "bg", args: {parameters: background_capabilities}}, options.success, options.error);
                /* MZ6 - No more "current" vs. queue -- still need to check queue
                }else if(this.active){
                    queue_endpoint.deferQuery({cmd: "cur", args: {parameters: module_capabilities}}, options.success, options.error);
                */
                }else{
                    console.log(this);
                    console.error("Unable to sync queue item");
                }
            }else if(method == "delete"){
                console.log("deleting", model)
                if(this.background){
                    //TODO - You can't actually delete backgrounds
                    console.error("How do I delete a background!?");
                    // Eh, try anyways
                    queue_endpoint.deferQuery({cmd: "rm", args: {uids: [model.id]}}, options.success, options.error);
                }else{
                    queue_endpoint.deferQuery({cmd: "rm", args: {uids: [model.id]}}, options.success, options.error);
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
        template: "unknown",
        background: false
    });

    var Background = Action.extend({
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
            queue_endpoint.deferQuery({cmd: "queue", args: {parameters: module_capabilities}}, options.success, options.error);
        }
    });

    var Volume = Backbone.Model.extend({
        defaults: {
            vol: 0,
        },
        initialize: function(prop, options){
            this.on('change:vol', function(model, vol, options){
                if(!options.parse){
                    volume_endpoint.deferQuery({cmd: "set_vol", args: { vol: vol }}); // FIXME: should sync on change
                }
            });
        },
        sync: function(method, model, options){
            if(method == "read"){
                volume_endpoint.deferQuery({cmd: "get_vol"}, options.success, options.error);
            }else{
                console.error("Can only read from volume"); // FIXME, should sync on change
            }
        },
    });

    var Musicazoo = Backbone.Model.extend({
        defaults: function(){
            return {
                queue: new Queue(),
                background: new Background(),
                volume: new Volume(),
            };
        },
        fetch: function(){
            this.get('queue').fetch();
            this.get('background').fetch();
            this.get('volume').fetch();
        }
    });

    var ActionView = Backbone.View.extend({
        act_template: Handlebars.compile("<a href='#' class='btn rm de-only'></a>{{{ html }}}"),
        events: {
            "click .rm": "remove",
            "click .cmd": "cmd",
            "click .action-set": "actionSet",
            "click .video-progress": "setProgress",
            "click .video-progress-bar": "setProgress",
            "click .youtube-add-related": "addRelatedYoutube",
            "mousedown .kbd": "keyDown",
            "touchstart .kbd": "keyDown",
            "mouseup .kbd": "keyUp",
            "touchend.kbd": "keyUp",
        },
        initialize: function(){
            var self = this;
            this.listenTo(this.model, "change", this.render);
            this.listenTo(this.model, "change:vid", function(){ self.model.unset("related"); } );
            this.render();
            return this;
        },
        render: function(ev){
            this.$el.html(this.act_template({
                html: TEMPLATES[this.model.template](this.model.attributes),
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
        keyDown: function(ev){
            var key = $(ev.target).attr('data-key');
            queue_endpoint.forceQuery({cmd: "tell_module", args: {uid: this.model.id, cmd: "key_down", args: {key: key}}});
        },
        keyUp: function(ev){
            var key = $(ev.target).attr('data-key');
            queue_endpoint.forceQuery({cmd: "tell_module", args: {uid: this.model.id, cmd: "key_up", args: {key: key}}});
        },
        addRelatedYoutube: function(ev){
            var self = this;
            var pushVideo = function(){
                var related = self.model.get('related');
                var rel = related.pop();
                queue_endpoint.deferQuery({cmd: 'add', args: {type: 'youtube', args: {url: rel.url}}});
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
                    // FIXME: this should go on Queue.sync
                    queue_endpoint.deferQuery({cmd: "mv", args:{uids: ordering}});
                    this.model.fetch();
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

            $("a.help").click(function(){
                $("div.help-sidebar").slideToggle();
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

    var VolumeView = Backbone.View.extend({
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

    mz = mz = new Musicazoo();
    var qv = new QueueView({collection: mz.get('queue'), el: $("ol.playlist")});
    var bv = new BackgroundView({model: mz.get('background'), el: $("ol.background")});
    var vv = new VolumeView({model: mz.get('volume')});

    mz.fetch();

    refreshPlaylist = function(){
        mz.fetch();
    }

    refreshPlaylist();
    // Refresh playlist every 1 seconds
    setInterval(refreshPlaylist, 1000);
    if(typeof(musicazooLoaded) != "undefined"){
        musicazooLoaded(mz);
    }
});

authenticate(authCallback);

/*
* With great power comes great responsibility

* ...but seriously don't fuck it up:
*
* - Don't toggle a light more than once every 2 seconds
* - Make sure all the lights are back on during the day
* - Something something fire code
* - Don't annoy your neighbors (unless it's really funny)
* - Don't get caught
*
*/

Lights = {
    groups: ["G", "B", "W"],
    set: function(name, relay, state){
        return lux_endpoint.forceQuery({cmd: "set_state", args: {name: name, relay: relay, new_state: !!state}});
    },
    groupSet: function(name, state){
        for(var i = 0; i < 12; i++){
            this.set(name, i, state);
        }
    },
    on: function(name, relay){
        this.set(name, relay, true);
    },
    off: function(name, relay){
        this.set(name, relay, false);
    },
    groupOn: function(name, relay){
        this.groupSet(name, true);
    },
    groupOff: function(name, relay){
        this.groupSet(name, false);
    },
}
