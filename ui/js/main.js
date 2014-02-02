$(document).ready(function() {
	setupRippers();
	setupAlbumFilters();
	loadSiteStatuses();
	pageChanged();
});

$(window).bind('popstate', function(e) {
	pageChanged();
	e.stopPropagation();
});

function loadSiteStatuses() {
	$('#supported-album')
		.empty()
		.load('./status.html', function() {
			$(this).slideDown(200);
		});
	$('#supported-video')
		.empty()
		.load('./status_video.html');
}

function pageChanged() {
	$('a:focus').blur(); // Blur focused link
	$(window).unbind('scroll'); // Stop any pages from infinite scrolling when hidden
	var keys = getQueryHashKeys();
	if      ('stats'   in keys) { showPage('page-stats'); }
	else if ('site'    in keys) { showPage('page-about-site'); }
	else if ('terms'   in keys) { showPage('page-about-terms'); }
	else if ('removal' in keys) { showPage('page-about-removal'); }
	else if ('code'    in keys) { showPage('page-about-code'); }
	else if ('albums'  in keys) {
		loadAlbums(keys);
	}
	else if ('album' in keys) {
		loadAlbum(keys.album);
	}
	else if ('user' in keys) {
		$('#filter-button')
			.html('user: ' + keys.user + ' <span class="caret"></span>')
			.attr('filtername', keys.user);
		showPage('page-albums');
		applyAlbumsFilter();
	}
	else if ('reports' in keys) {
		$('#sort-button')
			.html('reports <span class="caret"></span>')
			.attr('filtername', 'reports');
		showPage('page-albums');
		applyAlbumsFilter();
	}
	else if ('video'   in keys) {
		showPage('page-video');
		startVideoRip(keys['video']);
	}
	else if (window.location.hash.indexOf('.') >= 0 || window.location.hash.indexOf('gonewild:') >= 0) {
		// Page to rip
		showPage('page-rip');
		startAlbumRip(window.location.hash.substring(1));
	}
	else {
		showPage('page-rip');
		$('#text-rip-album').val('');
		$('#button-rip-album, #text-rip-album').removeAttr('disabled');
		$('#status-rip-album').html('');
	}
}

function loadAlbums(keys) {
	var scrollTop = $('#page-albums').data('scroll');
	if (scrollTop === undefined) {
		scrollTop = 0;
	}
	$(window)
		.unbind('scroll')
		.scroll(albumsScrollHandler);
	showPage('page-albums', scrollTop, albumsScrollHandler);
}

function addAlbumPreview(path, album) {
	var $div = $('<div/>')
		.addClass('col-xs-12 col-md-6 col-lg-6 text-center well album-preview')
		.data('album', path)
		.click(function() {
			// Save current scroll location
			$('#page-albums').data('scroll', $(window).scrollTop());
			// View album
			window.location.hash = 'album=' + $(this).data('album');
		});
		
	$('<div/>')
		.addClass('col-xs-12')
		.append( $('<h3 style="white-space: nowrap; x-overflow: hidden"/>').html(
				'<small class="albums-host">' + album.host + '/</small> ' + 
				' <span class="albums-name">' + album.name.replace(' ', '&nbsp;') + '</span>' +
				' <small class"albums-count">(' + album.count + '&nbsp;images)</small>')
			)
		.appendTo( $div );

	for (var i in album.preview) {
		var image = album.preview[i];
		var ratio = 160 / image.t_height;
		image.t_height *= ratio;
		image.t_width *= ratio;
		$('<div/>')
			.addClass('col-xs-12 col-sm-3 col-md-6 col-lg-3 thumbnail')
			.append(
				$('<img/>')
					.attr('src', image.thumb)
					.css({
						'width'  : image.t_width,
						'height' : image.t_height
					})
				)
			.appendTo($div)
			.hide()
			.slideDown(200)
			.data('image', image)
			.click(function(e) {
				e.stopPropagation();
				var img = $(this).data('image');
				var w = img.width, h = img.height;
				var ratio = $(window).width() / img.width;
				w *= ratio; h *= ratio;
				var t = $(window).scrollTop() + Math.max($('.navbar').height(), ($(window).height() / 2) - (h / 2));
				var l = 0;
				if (h > $(window).height()) {
					var ratio = $(window).height() / img.height;
					w = img.width, h = img.height;
					w *= ratio; h *= ratio;
					l = ($(window).width() / 2) - (w / 2);
				}
				$('#albums-image')
					.css({
						width: w,
						height: h,
						top: t,
						left: l
					});
				var $full = $('<img/>')
					.css({
						'width': '100%',
						'height': '100%'
					})
					.attr('src', img.image)
				$('#albums-image')
					.empty()
					.append( $full )
					.stop()
					.slideDown(200)
					.click(function() {
						$(this).stop().slideUp(200)
					});
			});
	}
	if ('admin' in album && 'reports' in album.admin && album.admin.reports > 0) {
		$div.css('background-color', '#b77');
		$('<span/>')
			.html('<b>' + album.admin.reports + ' report' + (album.admin.reports == 1 ? '' : 's') + '</b>')
			.css({
				'position': 'absolute',
				'left': $div.width() / 2,
				'font-size' : '1.2em'
			})
			.appendTo( $div );
	}
	$div
		.appendTo( $('#albums-container') );
}

function albumsScrollHandler() {
	var page     = $(document).height(); // Height of document
	var viewport = $(window).height();   // Height of viewing window
	var scroll   = $(document).scrollTop() || window.pageYOffset; // Scroll position (top)
	var remain = page - (viewport + scroll);
	if (viewport > page || // Viewport is bigger than entire page
	    remain < 300) {    // User has scrolled down far enough
		loadMoreAlbums();
	}
}

function loadMoreAlbums() {
	var loading = $('#page-albums').data('loading');
	if (loading !== undefined && loading) {
		// Currently waiting for more albums to load, don't try to load more
		return;
	}
	var params = $('#page-albums').data('params');
	if (params === undefined) {
		params = {
			'start': 0,
			'count': 6,
			'method': 'get_albums'
		};
	}
	if (params.finished !== undefined) {
		// Hit end of albums
		return;
	}
	$('#page-albums').data('loading', true);
	$('#albums-status').html( getSpinner(100) );
	$.getJSON('api.cgi?' + $.param(params))
		.fail(function() { /* TODO */ })
		.done(function(json) {
			if (json === null) { json = {'error' : 'null response'}; }
			if ('error' in json) {
				// TODO Handle error
				$('#album-info-name')
					.html(json.error + ' <small>error</small>')
					.slideDown(200);
				throw new Error(json.error);
			}
			if ('albums' in json) {
				for (var i in json.albums) {
					var path;
					for (path in json.albums[i]) break; // Get first (only) key
					var album = json.albums[i][path];
					addAlbumPreview(path, album);
				}
				if (json.albums.length < params.count) {
					// We got empty/partial response. Means we're done
					$('#page-albums').data('params').finished = true;
					$(window).unbind('scroll');
				}
				$('#albums-status')
					.fadeOut(200, function() {
						$(this).fadeIn(200);
						$(this).html('loaded ' + (params.start - (params.count - json.albums.length)) + ' albums');
					})
				setTimeout(function() {
					$('#page-albums').data('loading', false);
					albumsScrollHandler();
				}, 500);
			}
			// Add list of hosts to albums filter
			if ('sites' in json) {
				for (var i in json.sites) {
					$('<a/>')
						.attr('id', 'albums-filter-' + json.sites[i])
						.html(json.sites[i])
						.click(function() {
							$('#filter-button')
								.attr('filtername', this.innerHTML)
								.html( this.innerHTML );
							applyAlbumsFilter();
						})
						.appendTo(
							$('<li/>')
								.appendTo( $('ul#album-filter') )
						)
				}
			}
		});
	// Set next value
	params.start += params.count;
	$('#page-albums').data('params', params);
}

function albumScrollHandler() {
	var page     = $(document).height(); // Height of document
	var viewport = $(window).height();   // Height of viewing window
	var scroll   = $(document).scrollTop() || window.pageYOffset; // Scroll position (top)
	var remain = page - (viewport + scroll);
	if (viewport > page || // Viewport is bigger than entire page
	    remain < 300) {    // User has scrolled down far enough
		loadAlbumImages();
	}
}

function loadAlbum(album) {
	showPage('page-album');
	$(window)
		.unbind('scroll');
	$('#album-container')
		.data('album', {
			'album' : album,
			'start' : 0,
			'count' : 12,
		})
		.empty();
	// Album info
	$('#album-info-table,#admin-info-table,#album-status,#album-info-rerip,#album-info-name').hide();
	$.getJSON('api.cgi?method=get_album_info&album=' + encodeURIComponent(album))
		.fail(function() { /* TODO */ })
		.done(function(json) {
			if (json === null) { json = {'error' : 'null response'}; }
			if ('error' in json) {
				$('#album-info-name')
					.html(json.error + ' <small>error</small>')
					.slideDown(200);
				if ('url' in json) {
					// Error contains a 'url'
					// TODO insert this below the album name
					$('#album-info-rerip').empty().show();
					$('<a/>')
						.attr('id', 'album-info-rerip-link')
						.attr('href', json.url)
						.attr('target', '_BLANK_' + json.host + json.album_name)
						.html(json.url + ' <span class="glyphicon glyphicon-new-window"></span>')
						.hide().slideDown(200)
						.appendTo( $('#album-info-rerip') );
					$('<button type="button" class="btn btn btn-primary" id="album-info-rerip-button"/>')
						.css('margin-left', '20px')
						.html('re-rip')
						.click(function() {
							window.location.hash = encodeURIComponent(json.url.replace('http://', ''));
						})
						.appendTo( $('#album-info-rerip') );
				}
				throw new Error(json.error);
			}
			// ALBUM INFO
			$('#album-info-table').slideDown(200);
			$('#album-info-name')
				.html('<small>' + json.host + '/</small> ' + json.album_name)
				.slideDown(200);
			$('#album-info-source')
				.empty()
				.append(
					$('<a/>')
						.attr('href', json.url)
						.attr('target', '_BLANK_' + json.host + json.album_name)
						.css({
							'font-weight': 'bold',
							'text-decoration': 'underline'
						})
						.html(json.url + ' <span class="glyphicon glyphicon-new-window"></span>')
				)
			// REPORT
			if ('already_reported' in json) {
				$('#album-report-drop')
					.attr('disabled', 'disabled')
					.html('album has been reported with reason "' + json.already_reported + '"');
			} else {
				$('#album-report-drop')
					.html('<b><span class="glyphicon glyphicon-flag"></span> report this album</b>')
					.removeAttr('disabled');
				$('#album-report-button')
					.data('album', album)
					.click(function() {
						reportAlbum( $(this).data('album'), $('#album-report-text').val() );
					});
			}
			$('#album-report-drop')
				.slideDown(200);

			// ZIP
			if (json.zip === undefined || json.zip === null) {
				/* TODO create zip button */
				$('#album-info-download').empty();
				$('<button type="button"/>')
					.addClass('btn btn-sm btn-primary')
					.html('<b><span class="glyphicon glyphicon-compressed"></span> zip</b>')
					.click(function() {
						$('#album-info-download')
							.empty()
							.append( getSpinner() );
						$.getJSON('api.cgi?method=generate_zip&album=' + encodeURIComponent($('#album-container').data('album')['album']))
							.fail(function() {
								$('#album-info-download').html('failed to create zip');
							})
							.done(function(json) {
								$('<button/>')
									.attr('type', 'button')
									.addClass('btn btn-sm btn-primary')
									.data('zip', json.zip)
									.click(function() {
										window.location.href = $(this).data('zip');
									})
									.html('<b><span class="glyphicon glyphicon-compressed"></span> zip</b>')
									.appendTo( $('#album-info-download').empty() );
								window.location.href = json.zip;
							});
					})
					.appendTo( $('#album-info-download') );
			} else {
					$('<button/>')
						.attr('type', 'button')
						.addClass('btn btn-sm btn-primary')
						.data('zip', json.zip)
						.click(function() {
							window.location.href = $(this).data('zip');
						})
						.html('<b><span class="glyphicon glyphicon-compressed"></span> zip</b>')
						.appendTo( $('#album-info-download').empty() );
			}
			$('#album-info-size').html(json.count + ' images <small>(' + bytesToHR(json.filesize) + ')</small>');
			$('#album-info-created').html(new Date(json.created * 1000).toLocaleString());
			$('#album-container').data('album')['total_count'] = json.count;
			// "Get URLs" buttons
			$('#album-info-urls-text').hide();
			$('#album-info-urls-source,#album-info-urls-rarchives').removeClass('active').removeAttr('disabled');
			setupGetURLs('source',    json.host)
			setupGetURLs('rarchives', 'rarchives')

			// ADMIN stuff
			if ('admin' in json) {
				$('#admin-info-table').slideDown(200);
				$('#admin-info-user').html(json.admin.user.ip);
				if ('banned' in json.admin.user && json.admin.user.banned) {
					$('#admin-info-banned').show();
					$('#admin-info-banned-reason').html('reason: "' + json.admin.user.banned_reason + '" ');
					$('<button class="btn btn-xs btn-success"/>')
						.attr('id', 'album-unban-user')
						.html('unban')
						.click(function() {
							$.getJSON('api.cgi?method=ban_user&user=' + json.admin.user.ip + '&unban=True')
								.fail(function() {
									$('#album-unban-user').html('failed to unban user');
								})
								.done(function(resp) {
									$('#album-unban-user')
										.attr('disabled', 'disabled')
										.html('user was unbanned');
								});
						})
						.appendTo( $('#admin-info-banned-reason') );
				} else {
					$('#admin-info-banned').hide();
				}
				if (json.admin.user.warnings > 0) {
					$('#admin-info-warned').show();
					$('#admin-info-warned-reason').html(json.admin.user.warnings + ' warnings, msg: "' + json.admin.user.warning_message + '" ');
					$('<button class="btn btn-xs btn-success"/>')
						.attr('id', 'album-unwarn-user')
						.html('clear')
						.click(function() {
							$.getJSON('api.cgi?method=warn_user&user=' + json.admin.user.ip + '&unwarn=True')
								.fail(function() {
									$('#album-unwarn-user').html('failed to remove warnings');
								})
								.done(function(resp) {
									$('#album-unwarn-user')
										.attr('disabled', 'disabled')
										.html('warnings were removed');
								});
						})
						.appendTo( $('#admin-info-warned-reason') );
				} else {
					$('#admin-info-warned').hide();
				}

				$('#admin-album-delete')
					.removeAttr('disabled')
					.click(function() {
						var p = {
							'method' : 'delete_album',
							'host'   : json.host,
							'album'  : json.album_name,
							'blacklist' : false
						};
						$(this).attr('disabled', 'disabled');
						$.getJSON('api.cgi?' + $.param(p))
							.fail(function() {
								$('#admin-album-delete')
									.removeClass()
									.addClass('btn btn-xs btn-danger')
									.html('failed to delete album');
							})
							.done(function(resp) {
								$('<div/>')
									.addClass('text-' + resp.color)
									.html(resp.message)
									.appendTo( $('#admin-album-area') );
							});
					});
				$('#admin-album-blacklist')
					.removeAttr('disabled')
					.click(function() {
						var p = {
							'method' : 'delete_album',
							'host'   : json.host,
							'album'  : json.album_name,
							'blacklist' : true
						};
						$(this).attr('disabled', 'disabled');
						$.getJSON('api.cgi?' + $.param(p))
							.fail(function() {
								$('#admin-album-blacklist')
									.removeClass()
									.addClass('btn btn-xs btn-danger')
									.html('failed to blacklist album');
							})
							.done(function(resp) {
								$('<div/>')
									.addClass('text-' + resp.color)
									.html(resp.message)
									.appendTo( $('#admin-album-area') );
							});
					});

				$('#admin-info-rip-count').html('<u><b><a href="#user=' + json.admin.user.ip + '">' + json.admin.user.rip_count + '</a></u></b>');
				$('#admin-user-delete-all')
					.removeAttr('disabled')
					.click(function() {
						var p = {
							'method' : 'delete_user',
							'user'   : json.admin.user.ip,
							'blacklist' : false
						};
						$(this).attr('disabled', 'disabled');
						$.getJSON('api.cgi?' + $.param(p))
							.fail(function() {
								$('#admin-user-delete-all')
									.removeClass()
									.addClass('btn btn-xs btn-danger')
									.html('failed to delete all albums');
							})
							.done(function(resp) {
								$('<div/>')
									.css('text-align', 'right')
									.html(resp.message)
									.appendTo( $('#admin-user-area') );
							});
					});
				$('#admin-user-blacklist-all')
					.removeAttr('disabled')
					.click(function() {
						var p = {
							'method' : 'delete_user',
							'user'   : json.admin.user.ip,
							'blacklist' : true
						};
						$(this).attr('disabled', 'disabled');
						$.getJSON('api.cgi?' + $.param(p))
							.fail(function() {
								$('#admin-user-blacklist-all')
									.removeClass()
									.addClass('btn btn-xs btn-danger')
									.html('failed to blacklist all albums');
							})
							.done(function(resp) {
								$('<div/>')
									.css('text-align', 'right')
									.html(resp.message)
									.appendTo( $('#admin-user-area') );
							});
					});

				if (json.admin.reports.length == 0) {
					$('#admin-info-reports')
						.removeClass('text-danger')
						.addClass('text-warning')
						.html('(none)');
				}
				else {
					$('#admin-info-reports')
						.removeClass('text-success')
						.addClass('text-danger')
						.empty();
					for (var i in json.admin.reports) {
						$('<div/>')
							.html(json.admin.reports[i].ip + ': "' + json.admin.reports[i].message + '"')
							.appendTo( $('#admin-info-reports') );
					}
				}

				var warn_params = {
					'method'  : 'warn_user',
					'user'    : json.admin.user.ip,
					'message' : $('#album-warn-text').val(),
					'url'     : json.url
				};
				$('#album-warn-button')
					.data('warn_params', warn_params)
					.click(function() {
						var warn_params = $(this).data('warn_params');
						warn_params.message = $('#album-warn-text').val();
						$('#admin-warn-form').siblings('div').remove();
						$.getJSON('api.cgi?' + $.param(warn_params))
							.fail(function() { 
								$('<div/>')
									.addClass('text-danger')
									.html('error: failed to warn user')
									.insertAfter('#admin-warn-form')
									.hide().slideDown(200);
							})
							.done(function(json) {
								$('<div/>')
									.addClass('text-' + json.color)
									.html(json.message)
									.insertAfter('#admin-warn-form')
									.hide().slideDown(200);
							});
					});

				var ban_params = {
					'method'  : 'ban_user',
					'user'    : json.admin.user.ip,
					'message' : $('#album-ban-text').val(),
					'url'     : json.url
				};
				$('#album-ban-button')
					.data('ban_params', ban_params)
					.click(function() {
						var ban_params = $(this).data('ban_params');
						ban_params.message = $('#album-ban-text').val();
						$('#admin-ban-form').siblings('div').remove();
						$.getJSON('api.cgi?' + $.param(ban_params))
							.fail(function() { 
								$('<div/>')
									.addClass('text-danger')
									.html('error: failed to ban user')
									.insertAfter('#admin-ban-form')
									.hide().slideDown(200);
							})
							.done(function(json) {
								$('<div/>')
									.addClass('text-' + json.color)
									.html(json.message)
									.insertAfter('#admin-ban-form')
									.hide().slideDown(200);
							});
					});
			}
			// Album progress, decides if thumbnails should be loaded
			checkAlbumProgress(album);
		});

}

function checkAlbumProgress(album) {
	if ( $('#page-album').data('progressing') !== true) {
		$('#page-album').data('progressing', true);
	}
	else if ( !$('#page-album').is(':visible') ) {
		// Stop if the page is no longer visible (user clicked away)
		$('#page-album').data('progressing', false);
		return;
	}
	$('#album-info-table').slideUp(200);
	$.getJSON('api.cgi?method=get_album_progress&album=' + encodeURIComponent(album))
		.fail(function() { /* TODO */ })
		.done(function(json) {
			$('#album-info-size').html(json.total + ' images <small>(' + bytesToHR(json.filesize) + ')</small>');
			if (json.completed + json.errored >= json.total) {
				// Album is completed, show album
				$('#page-album').data('progressing', false);
				$('#album-info-table').slideDown(200);
				$('#album-progress-container').slideUp(200);
				loadAlbumImages();
				$(window)
					.scroll(albumScrollHandler);
				return;
			}
			// Album is still in progress, hide fields and show status
			$('#admin-info-table').hide();
			$('#album-progress-container')
				.slideDown(200)
				.data('album', album);
			$('#album-progress-container span').slideDown(200);
			var perc = (json.completed / json.total);
			$('#album-progressbar-completed').css('width', (json.completed * 100/ json.total) + '%');
			$('#album-progressbar-pending').css('width',   ((json.pending + json.inprogress) * 100 / json.total) + '%');
			$('#album-progressbar-errored').css('width',   (json.errored * 100 / json.total) + '%');
			$('#album-progress-completed').html(json.completed);
			$('#album-progress-pending').html(json.pending + json.inprogress);
			$('#album-progress-errored').html(json.errored);
			$('#album-progress-elapsed').html(secondsToHR(json.elapsed));;
			// Refresh progress again
			setTimeout(function() {
				checkAlbumProgress( $('#album-progress-container').data('album') );
			}, 500);
		});
}

/** Sets up "source URLs" and "mirrored URLs" buttons */
function setupGetURLs(id, host) {
	if (host === 'gonewild') {
		$('#album-info-urls-' + id).attr('disabled', 'disabled');
		return;
	}
	$('#album-info-urls-' + id)
		.removeAttr('disabled')
		.html('<span class="glyphicon glyphicon-link"></span> urls (' + host + ')')
		.data('source', host)
		.data('id', id)
		.unbind('click')
		.click(function() {
			if ( $(this).hasClass('active') ) {
				$(this).removeClass('active');
				$(this).data('json').abort();
				$('#album-info-urls-text')
					.slideUp(200, function() {
						$('#album-info-urls').hide();
					});
				return;
			}
			$('button[id^="album-info-urls"]').removeClass('active');
			$(this)
				.addClass('active')
				.append( getSpinner(15) );
			if ( $('#album-info-urls-text').is(':visible') ) {
				$('#album-info-urls-text').stop().slideUp(200);
			}
			var url = 'api.cgi?method=get_album_urls&album=' + encodeURIComponent($('#album-container').data('album')['album']) + '&source=' + $(this).data('id');
			$(this).data('json', 
				$.getJSON(url)
					.always(function() { 
						$('#album-info-urls-' + id)
							.empty()
							.html('<span class="glyphicon glyphicon-link"></span> urls (' + host + ')')
					})
					.fail(function() {
						$('#album-info-urls').stop().show();
						$('#album-info-urls-text')
							.val('failed to retrieve images')
							.stop().hide()
							.slideDown(500);
					})
					.done(function(json) {
						$('#album-info-urls').show();
						var fontSize = $('#album-info-urls-text').css('font-size');
						var lineHeight = Math.floor(parseInt(fontSize.replace('px','')) * 1.5);
						$('#album-info-urls-text')
							.css('height', (15 + lineHeight * Math.min(json.length, 20)) + 'px')
							.val(json.join('\n'))
							.stop().hide()
						.slideDown(500);
					})
				);
		});
}

function loadAlbumImages() {
	var albumdata = $('#album-container').data('album');
	if (albumdata.loading || albumdata.loaded) return;
	albumdata.loading = true;
	if (albumdata.start  === undefined) albumdata.start = 0;
	if (albumdata.count  === undefined) albumdata.count = 12;
	if (albumdata.sort   === undefined) albumdata.sort = 'accessed';
	if (albumdata.order  === undefined) albumdata.order = 'descending';
	if (albumdata.host   === undefined) albumdata.host = undefined;
	if (albumdata.author === undefined) albumdata.author = undefined;
	var params = {
		method : 'get_album',
		album  : encodeURIComponent(albumdata.album),
		start  : albumdata.start,
		count  : albumdata.count,
		sort   : albumdata.sort,
		order  : albumdata.order,
		host   : albumdata.host,
		author : albumdata.author
	}
	albumdata.start += albumdata.count;
	$('#album-status').html( getSpinner(100) );
	$.getJSON('api.cgi?' + $.param(params))
		.fail(function() { /* TODO */ })
		.done(function(json) {
			if ('error' in json) {
				// TODO Handle error
				$('#album-info-name')
					.html(json.error + ' <small>error</small>')
					.slideDown(200);
				throw new Error(json.error);
			}
			var image;
			for (var i in json) {
				image = json[i];
				addAlbumImage(image);
			}
			$('#album-status')
				.slideDown(200)
				.html( (albumdata.start - albumdata.count + json.length) + '/' + (albumdata.total_count) + ' items loaded');
			if (albumdata.total_count !== undefined && 
			    albumdata.total_count <= albumdata.start) {
				// Done loading this album
				albumdata.loaded = true;
				$(window).unbind('scroll');
			}
			setTimeout(function() {
				$('#album-container').data('album').loading = false;
			}, 500);
		});
}

function addAlbumImage(image) {
	var $a = $('<a/>')
		.attr('href', image.image)
		.css('background-color', 'rgba(0,0,0,0.0)')
		.addClass('thumbnail');
	if (image.error !== null) {
		// Image isn't found. Show what we have on it anyway
		image.image = image.url;
		image.width = 160;
		image.height = 80;
		image.thumb = './ui/images/nothumb.png';
		image.twidth = 200;
		image.theight = 200;
	}
	// Expand image to have height 200px
	var ratio = 200 / image.theight;
	image.theight *= ratio;
	image.twidth *= ratio;
	var $img = $('<img/>')
		.attr('src', image.thumb)
		.css({
			'width'  : image.twidth + 'px',
			'height' : image.theight + 'px',
		})
		.data('image', {
			'image'   : image.image,
			'width'   : image.width,
			'height'  : image.height,
			'thumb'   : image.thumb,
			'twidth'  : image.twidth,
			'theight' : image.theight,
			'filesize': image.filesize,
			'url'     : image.url
		})
		.appendTo( $a )
		.slideDown(1000);
	$('<div/>')
		.addClass('col-xs-12 col-sm-6 col-md-4 col-lg-3 text-center')
		.append( $a )
		.appendTo( $('#album-container') )
		.click(function(e) {
			var imgdata = $(this).find('img').data('image');
			// Caption
			var $caption = $('<div/>')
				.append(
					$('<p/>').append(
						$('<a/>')
							.attr('href', imgdata.url)
							.attr('target', '_BLANK_' + imgdata.url)
							.attr('rel', 'noreferrer')
							.click(function(e) { 
								e.stopPropagation();
								window.open(imgdata.url);
								return false;
							})
							.html(imgdata.url)
					)
				);
			var w = imgdata.width, h = imgdata.height;
			var ratio = $(window).width() / w;
			w *= ratio; h *= ratio;
			var t = $(window).scrollTop() + Math.max($('.navbar').height(), ($(window).height() / 2) - (h / 2));
			$('#album-image')
				.css({
					width: w + 'px',
					height: h + 'px',
					top: t
				});
			var $full = $('<img/>')
				.attr('src', imgdata.image)
				.css({
					'width': '100%',
					'height': '100%'
				});
			$('#album-image')
				.empty()
				.append( $full )
				.append( $caption )
				.stop()
				.slideDown(500)
				.click(function() {
					$(this).stop().slideUp(200)
				});
			return false;
		});
	$('<div class="caption"/>')
		.html(image.width + '<small>x</small>' + image.height + ' (' + bytesToHR(image.filesize) + ')')
		.appendTo( $a );
}

function getSpinner(size) {
	if (size === undefined) size = 30;
	return $('<img/>')
		.attr('src', 'ui/images/spinner.gif')
		.css({
			'width'  : size + 'px',
			'height' : size + 'px',
			'margin-left'  : '5px',
			'margin-right' : '5px',
		});
}

function startAlbumRip(baseurl) {
	var url = decodeURIComponent(baseurl);
	if (url.indexOf('http') != 0) {
		url = 'http://' + url;
	}
	$('#text-rip-album')
		.val(url);
	$('#text-rip-album,#button-rip-album')
		.attr('disabled', 'disabled');
	$('#status-rip-album')
		.html(' getting album info...')
		.prepend( getSpinner() )
		.hide()
		.fadeIn(500);
	var request = 'api.cgi?method=rip_album&url=' + encodeURIComponent(url)
	var ajax = $.getJSON(request)
		.fail(function() { /* TODO */ })
		.done(function(json) {
			$('#button-rip-album').removeData('ajax');
			if ('error' in json) {
				$('#status-rip-album')
					.addClass('text-danger')
					.html(json.error);
				if ('trace' in json) {
					$('<div class="text-left" style="line-height: 1.0em"/>')
						.append( $('<small/>').html(json.trace) )
						.appendTo( $('#status-rip-album') );
				}
			}
			else {
				if ('warning' in json) {
					$('#status-rip-album').empty();
					$('<div class="text-warning"/>')
						.html(json.warning)
						.prepend( getSpinner() )
						.prependTo( $('#status-rip-album') );
				}
				else {
					$('#status-rip-album')
						.html('images retrieved, ripping will start momentarily')
						.prepend( getSpinner() );
				}
				// Redirect to album
				setTimeout(function() {
					window.location.hash = 'album=' + json.path;
				}, 1500);
			}
			$('#text-rip-album,#button-rip-album').removeAttr('disabled');
		});
	$('#button-rip-album').data('ajax', ajax);
}

function abortRip() {
	var ajax = $('#button-rip-album').data('ajax');
	if (ajax !== undefined) {
		ajax.abort();
	}
	$('#text-rip-album').val('');
	$('#button-rip-album, #text-rip-album').removeAttr('disabled');
	$('#status-rip-album').html('');
}

/** Hide current page, show page with 'id' */
function showPage(id, scrollTo, callback) {
	if (scrollTo === undefined) scrollTo = 0;
	if ( $('body [id^="page-"]:visible').attr('id') === id) {
		// Page is already showing
		$('html,body').stop().animate({ 'scrollTop': scrollTo }, 500);
		if (callback !== undefined) {
			callback();
		}
		return;
	}
	// Hide current page(s)
	$('body [id^="page-"]:visible')
		.stop()
		.slideUp(200, function() {
			// Show the page
			$('#' + id)
				.stop()
				.hide()
				.slideDown(400, function() {
					$('html,body')
						.stop()
						.animate({ 'scrollTop': scrollTo }, 200);
					if (callback !== undefined) {
						callback();
					}
				})
		});

	// Deselect nav-bar
	$('a[id^="nav-"]').parent().removeClass('active');
	$('a[id^="nav-' + id.split('-')[1] + '"]').parent().addClass('active');
	// Hide drop-down navbar (xs view)
	if ( $('.navbar-collapse').hasClass('in') ) {
		$('.navbar-toggle').click();
	}
}

/* Convert keys in hash to JS object */
function getQueryHashKeys() {
	var a = window.location.hash.substring(1).split('&');
	if (a == "") return {};
	var b = {};
	for (var i = 0; i < a.length; ++i) {
		var keyvalue = a[i].split('=');
		var key = keyvalue[0];
		keyvalue.shift(); // Remove first element (key)
		var value = keyvalue.join('='); // Remaining elements are the value
		b[key] = decodeURIComponent(value); //.replace(/\+/g, " "));
	}
	return b;
}

/** Format numbers > 999 to contain commas in thousands-places */
function addCommas(x) {
	return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function setupRippers() {
	// Album ripper
	$('#button-rip-album')
		.click(function() {
			$('#text-rip-album').blur();
			var url = $('#text-rip-album').val();
			url = url.replace(/https?:\/\/(www\.)/, '');
			window.location.hash = url;
		});
	$('#text-rip-album')
		.keydown(function(e) {
			if (e.keyCode === 13) {
				$('#button-rip-album').click();
			}
		});

	// Video ripper
	$('#button-rip-video')
		.click(function() {
			$('#text-rip-video').blur();
			var url = $('#text-rip-video').val()
			// JS automatically converts encoded chars in hash
			// So we're going to use a flag to denote &amp;
			url = url.replace('&', '||AMP||'); 
			window.location.hash = 'video=' + encodeURIComponent(url);
		});
	$('#text-rip-video')
		.keydown(function(e) {
			if (e.keyCode === 13) {
				$('#button-rip-video').click();
			}
		});
}

function startVideoRip(url) {
	if (url === '') {
		$('#text-rip-video').val('');
		return;
	}
	url = url.replace('||AMP||', '&'); // Convert flags back to &amp;
	if (url.indexOf('http') != 0) {
		url = 'http://' + url;
	}
	$('#text-rip-video').val(decodeURIComponent(url));
	$('#video-info-container')
		.slideUp(200);
	url = encodeURIComponent(url);
	$('#status-rip-video')
		.removeClass()
		.html(' getting video info...')
		.prepend( getSpinner() )
		.hide()
		.slideDown(500);
	$.getJSON('api.cgi?method=rip_video&url=' + url)
		.fail(function() { /* TODO */ })
		.done(function(json) {
			if ('error' in json) {
				// TODO show error
				$('#status-rip-video')
					.addClass('text-danger')
					.html(json.error)
					.hide()
					.slideDown(200);
				if ('trace' in json) {
					$('<div class="text-left" style="line-height: 1.0em"/>')
						.append( $('<small/>').html(json.trace) )
						.appendTo( $('#status-rip-video') );
				}
				return;
			}
			$('#status-rip-video')
				.removeClass()
				.slideUp(200, function() { $(this).empty() });
			$('#video-title').html(json.host + ' <small>' + json.source.replace('http://', '').replace('www.', '').replace(json.host, '') + '</small>');
			$('#video-info-url')
				.empty()
				.append(
					$('<a/>')
						.data('url', json.url)
						.attr('href', json.url)
						.attr('rel', 'noreferrer')
						.attr('target', '_BLANK_' + json.host)
						.mousedown(function(e) {
							if (e.which === 1) {
								$(this)
									.attr('href',
										'data:text/html;charset=utf-8,\n\n' +
										'<html><head><meta http-equiv=\'REFRESH\' content=\'0;url=' +
										json.url +
										'\'></head><body><h1>redirecting...</h1></body></html>\n\n')
							} else {
								$(this).attr('href', $(this).data('url'));
							}
						})
						.html('<span class="glyphicon glyphicon-download"></span> <b>download</b>')
				);
			$('#video-info-size')
					.html( bytesToHR(json.size) );
			$('#video-info-type')
					.html(json.type);
			$('#video-info-container')
				.slideDown(500);

			// Show video
			$('#video-player-anchor').remove();
			$('#video-player-container').empty();
			$('<div/>')
				.html('<b>source:</b> ')
				.appendTo( $('#video-player-container') )
				.append(
						$('<a/>')
							.attr('href', json.source)
							.attr('target', '_BLANK_' + json.host)
							.attr('rel', 'noreferrer')
							.html(json.source)
				);
			if ('no_video' in json) {
				$('<p/>')
					.html('try the download link')
					.prependTo( $('#video-player-container') );
				$('<h3/>')
					.html('unable to stream video from site')
					.prependTo( $('#video-player-container') );
			}
			else {
				var $vid = $('<video/>');
				if ( $vid[0].canPlayType('video/' + json.type) !== '') {
					$vid
						.attr('id', 'video-player-anchor')
						.attr('controls', 'controls')
						.css('width', '100%')
						.prependTo( $('#video-player-container') );
					$('<source/>')
						.attr('src', json.url)
						.attr('type', 'video/' + json.type)
						.appendTo( $vid );
				}
				else {
					// Can't play this type, default to flash
					var flowplayer_id = 'video-player-anchor',
							flowplayer_swf = 'ui/swf/flowplayer-3.2.18.swf',
							flowplayer_config = {
								onLoad: function() {
									this.setVolume(30);
								},
								clip: {
									autoPlay: false,
									autoBuffering: true,
									onMetaData: function(clip) {
										var w = parseInt(clip.metaData.width, 100);
										var h = parseInt(clip.metaData.height, 100);
										var ratio = $(window).width() / w;
										h = h * ratio;
										$(this.getParent()).css({
											width: w,
											height: h
										});
									}
								}
							};
					$vid.hide();
					$('<a/>')
						.attr('href', json.url)
						.css({
							'width'   : '100%',
							'height'  : '400px',
							'display' : 'block',
							'margin'  : '10px auto'
						})
						.attr('id', flowplayer_id)
						.prependTo( $('#video-player-container') );
					if ( $('#video-script').size() == 0) {
						$('<div id="video-script" style="display: none" />').appendTo( $('body') );
						$.getScript('ui/js/flowplayer-3.2.13.min.js')
							.done(function() {
								flowplayer(flowplayer_id, flowplayer_swf, flowplayer_config);
							});
					}
					else {
						flowplayer(flowplayer_id, flowplayer_swf, flowplayer_config);
					}
				}
			}
		});
}

function reportAlbum(album, reason) {
	$('#album-report')
		.slideUp(200);
	$('#album-report-drop')
		.attr('disabled', 'disabled')
		.html(getSpinner(20) + ' reporting...')
		.slideDown(200);
		
	var url = 'api.cgi?method=report_album&album=' + encodeURIComponent(album) + '&reason=' + encodeURIComponent(reason);
	$.getJSON(url)
		.fail(function() {
			$('#album-report-drop')
				.removeAttr('disabled')
				.html('failed to report album. click to try again');
		})
		.done(function(json) {
			$('#album-report-drop')
				.html(json.error)
		});
}

function setupAlbumFilters() {
	var fields;
	$.each($('#page-albums a[id^="albums-"]'), function(index, a) {
		$(a).click(function() {
			if ( $(a).attr('filtername') === 'asc' ) {
				$('#filter-sort-glyph')
					.removeClass('glyphicon-sort-by-attributes-alt')
					.addClass('glyphicon-sort-by-attributes');
			}
			else if ( $(a).attr('filtername') === 'desc' ) {
				$('#filter-sort-glyph')
					.removeClass('glyphicon-sort-by-attributes')
					.addClass('glyphicon-sort-by-attributes-alt');
			}

			$(this)
				.parent()
				.parent()
				.parent()
				.find('button')
					.html(this.innerHTML + ' <span class="caret"></span>')
					.attr('filtername', $(this).attr('filtername'));
			applyAlbumsFilter();
		});
	});
}

function applyAlbumsFilter() {
	var host = $('#filter-button').attr('filtername');
	var author;
	if (host === 'none') {
		host   = undefined;
		author = undefined;
	}
	else if (host === 'mine' || host.indexOf('.') >= 0 || host.indexOf(':') >= 0) {
		host   = undefined;
		author = host;
	}
	else {
		author = undefined;
	}

	$('#page-albums').data('params', {
		'host'   : host,
		'author' : author,
		'sort'   : $('#sort-button').attr('filtername'),
		'order'  : $('#order-button').attr('filtername'),
		'start'  : 0,
		'count'  : 6,
		'method' : 'get_albums',
		'finished' : undefined
	})
	.data('loading', undefined);

	$('#albums-container')
		.empty();
	loadMoreAlbums();
	$(window)
		.unbind('scroll')
		.scroll(albumsScrollHandler);
}

function bytesToHR(bytes) {
	var units = ['g', 'm', 'k', ''];
	var chunk = 1024 * 1024 * 1024;
	for (var unit in units) {
		if (bytes >= chunk) {
			return (bytes / chunk).toFixed(2) + units[unit] + 'b';
		}
		chunk /= 1024;
	}
	return '?b';
}

function secondsToHR(sec) {
	var units = {
		31536000: 'yr',
		2592000 : 'mon',
		86400   : 'day',
		3600    : 'hr',
		60      : 'min',
		1       : 'sec'
	};
	for (var unit in units) {
		if (sec > unit) {
			var hr = Math.floor(sec / unit);
			return hr + units[unit];
		}
	}
	return '?s';
}	
