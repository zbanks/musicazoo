var volume_lockout = false;
setInterval(function(){ volume_lockout = false; }, 500);

var _query_queue = [];
var _runquery_timeout;
var BASE_URL = "http://localhost:9000/";

function deferQuery(data, cb){
    _query_queue.push({"data": data, "cb": cb});
}

function forceQuery(data, cb){
    _query_queue.push({"data": data, "cb": cb});
    runQueries();
}

function runQueries(cb){
    window.clearTimeout(_runquery_timeout);
    if(_query_queue.length){
        var cbs = _.pluck(_query_queue, "cb");
        var datas = _.pluck(_query_queue, "data");
        $.post(BASE_URL, JSON.stringify(datas), function(resp){
            if(resp.length != cbs.length){ 
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

$(document).ready(function(){
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
    console.log(vm);
    ko.applyBindings(vm); 

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
            deferQuery({"cmd": "set_vol", "args": [ui.value], "target": vm.statics().volume.uid() }, function(){ volume_lockout = false; });
            console.log({"cmd": "set_vol", "args": [ui.value], "target": vm.statics().volume.uid() });
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


var mz_map = {
    playlist: {
        key: function(data){
            return ko.utils.unwrapObservable(data.id);
        }
    },
    current: {
        key: function(data){
            console.log(data.id);
            return ko.utils.unwrapObservable(data.id);
        }
    },
    observe: ['volume']
};

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


vm = new Musicazoo();
vm.statics.subscribe(function(nv){ console.log("STATIC HIT"); console.log(nv); });

var refreshPlaylist = function(firstTime){
    vm.reload();
}

refreshPlaylist(true);
// Refresh playlist every 1 seconds
setInterval(refreshPlaylist, 1000);


runQueries();
