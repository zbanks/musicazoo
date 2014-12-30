var player;
function playYoutubeVideo(id, time, isPaused, updateState) {
    var last_state = -1;
    player = new YT.Player('video', {
        height: '390',
        width: '640',
        events: {
            'onReady': function(ev){
                //ev.target.playVideo(); 
                if(isPaused){
                    player.cueVideoById(id, time);
                }else{
                    player.loadVideoById(id, time);
                }
                //ev.target.seekTo(time*1, true);
            },
            'onStateChange': function(ev){
                var state = ev.data;
                switch(ev.data){
                    case -1: // Unstarted
                    break;
                    case 0: // Ended
                    break;
                    case 1: // Playing
                        player.status = "playing";
                        if(last_state != state){
                            updateState(state);
                        }
                    break;
                    case 2: // Paused
                        player.status = "paused";
                        if(last_state != state){
                            updateState(state);
                        }
                    break;
                    case 3: // Buffering

                    break;
                    case 5: // Video Cued

                    break;
                    default: 
                    break;
                }
                last_state = state;
            }
        }
    });
    return player;
}


function musicazooLoaded(mz){
    console.log("Musicazoo: ", mz);
    var MirrorView = Backbone.View.extend({
        update_time: function(remote){
            if(this.player && this.player.getCurrentTime){
                var remote_time = this.model.get('time');
                var local_time = this.player.getCurrentTime();
                if(Math.abs(remote_time - local_time) > 5){
                    if(remote){
                        this.model.set('time', local_time);
                    }else{
                        this.player.seekTo(remote_time);
                    }
                }
            }
        },
        bindEvents: function(){
            this.listenTo(this.model, "change", function(model){
                /* XXX: Can't get change:time to work :( */
                console.log(model.attributes);
                if(this.model.get('type') == 'youtube'){
                    this.update_time(false);
                }
            });
            this.listenTo(this.model, "change:status", function(model, value, options){
                if((this.model.get('type') == 'youtube') && this.player){
                    if(value == 'paused'){
                        console.log("pausing");
                        this.player.pauseVideo();
                    }else if(value == 'playing'){
                        console.log("playing");
                        this.player.playVideo();
                    }
                }
            });
            this.listenTo(this.model, "change:exists", function(model, value, options){
                if(value == false){
                    if(this.player){
                        this.player.destroy();
                        this.player = null;
                        $('.video').html('');
                    }
                }
            });
        },
        initialize: function(params){
            var self = this;
            this.watcher = params.watcher;
            this.listenTo(this.watcher, "new-active", function(new_active, old_active){
                if(this.model)
                    this.stopListening(this.model);
                this.model = new_active;

                if(this.model)
                    this.bindEvents();

                if(this.player){
                    this.player.destroy();
                }

                $('.video').html('');
                console.log('hello', this.model.get('time'));
                if(this.model.get('type') == 'youtube'){
                    console.log(this.model.attributes);
                    var isPaused = this.model.get('status') == 'paused';
                    
                    this.player = playYoutubeVideo(this.model.get('vid'), this.model.get('time'), isPaused, function(state){
                        if(state == 1){
                            self.model.set('status', 'playing');
                            self.update_time(true);
                        }else if(state == 2){
                            self.model.set('status', 'paused');
                        }
                    });
                }else{
                    this.player = null;
                }
            });
            return this;
        }
    });

    var QueueWatcherView = Backbone.View.extend({
        initialize: function(){
            this.active = null;

            this.listenTo(this.collection, "add", this.update_active);
            this.listenTo(this.collection, "reset", this.update_active);
            this.listenTo(this.collection, "sort", this.update_active);
            this.listenTo(this.collection, "remove", this.update_active);

            this.update_active();
        },
        update_active: function(){
            var queue_top = this.collection.at(0);
            var prev_active = this.active;

            if(queue_top && this.active){
                if(queue_top.id != this.active){
                    this.active = queue_top;
                    this.trigger("new-active", this.active, prev_active);
                }
            }else if(queue_top || this.active){
                this.active = queue_top;
                this.trigger("new-active", this.active, prev_active);
            }
        }
    });

    var qw = new QueueWatcherView({collection: mz.get('queue')});
    var cv = new MirrorView({model: qw.active, watcher: qw, el: $(".display-area")});
}

