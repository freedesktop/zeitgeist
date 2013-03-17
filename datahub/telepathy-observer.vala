/*
 * Zeitgeist
 *
 * Copyright (C) 2012 Collabora Ltd.
 *               Authored by: Seif Lotfy <seif.lotfy@collabora.co.uk>
 * Copyright (C) 2012 Eslam Mostafa <cseslam@gmail.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

using Zeitgeist;
using TelepathyGLib;
using Json;

public class TelepathyObserver : DataProvider
{

  private const string actor = "dbus://org.freedesktop.Telepathy.Logger.service";
  private const string tp_account_path = "x-telepathy-account-path:%s";
  private const string tp_identifier = "x-telepathy-identifier:%s";
  private const string ft_json_domain = "http://zeitgeist-project.com/1.0/telepathy/filetransfer";
  private const string call_json_domain = "http://zeitgeist-project.com/1.0/telepathy/call";

  private TelepathyGLib.DBusDaemon dbus = null;
  private TelepathyGLib.AutomaticClientFactory factory = null;
  private TelepathyGLib.SimpleObserver observer = null;
  private HashTable<string, Timer> call_timers = null;

  public TelepathyObserver (DataHub datahub) throws GLib.Error
  {
    GLib.Object (unique_id: "com.zeitgeist-project,datahub,telepathy-observer",
                 name: "Telepathy Observer",
                 description: "Logs IM, call and filetransfer from telepathy",
                 datahub: datahub);
  }

  construct
  {
    call_timers = new HashTable<string, Timer> (str_hash, str_equal);
    try {
      dbus = TelepathyGLib.DBusDaemon.dup ();
    }
    catch (GLib.Error err)
    {
      warning ("Couldn't dup DBusDaemon: %s", err.message);
      return;
    }
    factory = new TelepathyGLib.AutomaticClientFactory (dbus);

    Quark[] channel_quark = {TelepathyGLib.Channel.get_feature_quark_contacts ()};
    TelepathyGLib.ContactFeature[] contact_quark = {TelepathyGLib.ContactFeature.ALIAS};

    factory.add_channel_features (channel_quark);
    factory.add_contact_features (contact_quark);
  }

  // if vala didn't have bug in construct-only properties, the properties
  // would be construct-only
  public override string unique_id { get; construct set; }
  public override string name { get; construct set; }
  public override string description { get; construct set; }

  public override DataHub datahub { get; construct set; }
  public override bool enabled { get; set; default = true; }
  public override bool register { get; construct set; default = true; }

  private void push_event (Event event)
  {
    GenericArray<Event> events = new GenericArray<Event> ();
    events.add (event);
    items_available (events);
  }

  /*
   * Create a standard template for text channel based events
   */
  private Event create_text_event (Account account, Channel channel)
  {
    var target = channel.get_target_contact ();
    var obj_path = account.get_object_path ();
    obj_path = tp_account_path.printf(obj_path[
      TelepathyGLib.ACCOUNT_OBJECT_PATH_BASE.length : obj_path.length]);
    Event event_template = new Event.full (
                              ZG.ACCESS_EVENT,
                              "",
                              actor,
                              null,
                              obj_path);

    /*
     * Whether user initiated the chat or not
     */
    if (!channel.requested)
      event_template.manifestation = ZG.WORLD_ACTIVITY;
    else
      event_template.manifestation = ZG.USER_ACTIVITY;

    /*
     * Create IM subject for the event
     */
    event_template.add_subject (
      new Subject.full (
        "",
        NMO.IMMESSAGE,
        NFO.SOFTWARE_SERVICE,
        "plain/text",
        tp_identifier.printf (target.get_identifier ()),
        "",
        "net")
      );

    /*
     * Create Contact subject for the event
     */
    event_template.add_subject (
      new Subject.full (
        tp_identifier.printf (target.get_identifier ()),
        NCO.CONTACT,
        NCO.CONTACT_LIST_DATA_OBJECT,
        "",
        obj_path,
        target.get_alias (),
        "net")
    );
    return event_template;
  }

  private void observe_text_channel (SimpleObserver observer, Account account,
                                 Connection connection, Channel b_channel,
                                 ChannelDispatchOperation? dispatch_operation,
                                 List<ChannelRequest> requests,
                                 ObserveChannelsContext context)
  {
    /*
     * Channel has been created
     */
    TextChannel channel = (TextChannel) b_channel;
    var target = channel.get_target_contact ();
    if (target != null)
    {
      /*
       * Create an event representing conversation start
       */
      var event_template = this.create_text_event (account, channel);
      this.push_event (event_template);
      /*
       * Process pending messages
       */
      foreach (var message in channel.get_pending_messages ())
      {
        if (!message.is_delivery_report ())
        {
          event_template = this.create_text_event (account, channel);
          event_template.interpretation = ZG.RECEIVE_EVENT;
          event_template.manifestation = ZG.WORLD_ACTIVITY;
          this.push_event (event_template);
        }
        // FIXME: what about sent messages? what happens with them?
      }
      /*
       * Connect to the signal representing conversation end
       */
      channel.invalidated.connect (() => {
        event_template = this.create_text_event (account, channel);
        // manifestation depends on the chat creator, unless we can
        // get a better value.
        event_template.interpretation = ZG.LEAVE_EVENT;
        this.push_event (event_template);
      });
      /*
       * Connect to receive message signals of the channel
       */
      channel.message_received.connect (() => {
        event_template = this.create_text_event (account, channel);
        event_template.interpretation = ZG.RECEIVE_EVENT;
        event_template.manifestation = ZG.WORLD_ACTIVITY;
        this.push_event (event_template);
      });
      /*
       * Connect to send message signals of the channel
       */
      channel.message_sent.connect (() => {
        event_template = this.create_text_event (account, channel);
        event_template.interpretation = ZG.SEND_EVENT;
        event_template.manifestation = ZG.USER_ACTIVITY;
        this.push_event (event_template);
      });
    }
  }

  /*
   * Create a standard template for call channel based events
   */
  private Event? create_call_event (Account account, CallChannel channel)
  {
    var targets = channel.get_members ();
    if (targets == null)
      return null;
    weak TelepathyGLib.Contact? target = targets.get_keys ().data;

    var obj_path = account.get_object_path ();
    obj_path = tp_account_path.printf(obj_path[
      TelepathyGLib.ACCOUNT_OBJECT_PATH_BASE.length : obj_path.length]);
    Event event_template = new Event.full (
                              ZG.ACCESS_EVENT,
                              ZG.USER_ACTIVITY,
                              actor,
                              null,
                              obj_path);
    if (!channel.requested)
      event_template.manifestation = ZG.WORLD_ACTIVITY;
    /*
     * Create Call subject for the event
     */
    event_template.add_subject (
      new Subject.full (
        "",
        NFO.AUDIO,
        NFO.MEDIA_STREAM,
        "x-telepathy/call",
        tp_identifier.printf (target.get_identifier ()),
        target.get_alias (),
        "net")
    );
    /*
     * Create Contact subject for the event
     */
    event_template.add_subject (
      new Subject.full (
        tp_identifier.printf(target.get_identifier ()),
        NCO.CONTACT,
        NCO.CONTACT_LIST_DATA_OBJECT,
        "",
        obj_path,
        target.get_alias (),
        "net")
    );
    return event_template;
  }

  private void observe_call_channel (SimpleObserver observer, Account account,
                                     Connection connection, Channel b_channel,
                                     ChannelDispatchOperation? dispatch_operation,
                                     List<ChannelRequest> requests,
                                     ObserveChannelsContext context)
  {
    CallChannel channel = (CallChannel) b_channel;

    channel.state_changed.connect (() =>
      {
        CallFlags flags;
        TelepathyGLib.CallStateReason reason;
        CallState state = channel.get_state (out flags, null, out reason);

        /*
         * Create an Event template for call events
         */
        var event_template = this.create_call_event (account, channel);

        /*
         * Start operating once the call state is initialized
         */
        if (state == TelepathyGLib.CallState.INITIALISED)
        {
          event_template.interpretation = ZG.CREATE_EVENT;
          Timer t = new Timer ();
          t.stop ();
          call_timers.insert (channel.get_object_path (), (owned) t);
          this.push_event (event_template);
        }
        /*
         * Act only on call active or call end
         */
        else if ((state == TelepathyGLib.CallState.ACTIVE || state == TelepathyGLib.CallState.ENDED)
                  && call_timers.contains (channel.get_object_path ()))
        {
          if (state == TelepathyGLib.CallState.ACTIVE)
          {
            event_template.interpretation = ZG.ACCESS_EVENT;
            call_timers.lookup (channel.get_object_path ()).start();
            this.push_event (event_template);
          }
          else if (state == TelepathyGLib.CallState.ENDED)
          {
            event_template.interpretation = ZG.LEAVE_EVENT;

            /* Call was created by user but was rejected or not answered */
            if (reason.reason == TelepathyGLib.CallStateChangeReason.REJECTED
                || reason.reason == TelepathyGLib.CallStateChangeReason.NO_ANSWER)
            {
              if (channel.requested)
                event_template.manifestation = ZG.WORLD_ACTIVITY;
              else
                event_template.interpretation = ZG.USER_ACTIVITY;

              if (reason.reason == TelepathyGLib.CallStateChangeReason.NO_ANSWER)
                event_template.interpretation = ZG.EXPIRE_EVENT;
              else
                event_template.interpretation = ZG.DENY_EVENT;
            }

            var duration  = call_timers.lookup (channel.get_object_path ()).elapsed ();
            call_timers.lookup (channel.get_object_path ()).stop;
            call_timers.remove (channel.get_object_path ());
            /*
             * Create JSON payload representing the call metadata including
             * duration and termination reasons of the call.
             */
            var gen = new Generator();
            var root = new Json.Node(NodeType.OBJECT);
            var object = new Json.Object();
            root.set_object(object);
            gen.set_root(root);
            gen.pretty = true;

            var details_obj = new Json.Object ();
            details_obj.set_int_member ("state", state);
            details_obj.set_int_member ("reason", reason.reason);
            details_obj.set_boolean_member ("requested", channel.requested);
            details_obj.set_double_member ("duration", duration);
            size_t length;
            object.set_object_member (call_json_domain, details_obj);
            string payload_string = gen.to_data(out length);
            event_template.payload = new GLib.ByteArray.take (payload_string.data);
            this.push_event (event_template);
          }
        }
      });
  }

  private async void handle_ftchannel_change (SimpleObserver observer,
                                              Account account,
                                              Connection connection,
                                              FileTransferChannel channel,
                                              ChannelDispatchOperation? dispatch_operation,
                                              List<ChannelRequest> requests,
                                              ObserveChannelsContext context)
  {
    if (channel.state == TelepathyGLib.FileTransferState.COMPLETED
        || channel.state == TelepathyGLib.FileTransferState.CANCELLED)
      {
        var target = channel.get_target_contact ();
        var attr = "%s, %s, %s".printf (FileAttribute.STANDARD_DISPLAY_NAME,
          FileAttribute.STANDARD_CONTENT_TYPE, FileAttribute.STANDARD_SIZE);
        FileInfo info = null;
        try
        {
          info = yield channel.file.query_info_async (attr, 0);
        }
        catch (GLib.Error err)
        {
          warning ("Couldn't process %s: %s", channel.file.get_path (), err.message);
          return;
        }
        var obj_path = account.get_object_path ();
        obj_path = tp_account_path.printf("%s",
                   obj_path [TelepathyGLib.ACCOUNT_OBJECT_PATH_BASE.length:
                   obj_path.length]);
        /* Create Event template */
        var event_template = new Event ();
        if (channel.requested)
        {
          event_template.interpretation = ZG.SEND_EVENT;
          event_template.manifestation = ZG.USER_ACTIVITY;
        }
        else
        {
          event_template.interpretation = ZG.RECEIVE_EVENT;
          event_template.manifestation = ZG.WORLD_ACTIVITY;
        }
        event_template.actor = actor;
        /*
         * Create Subject representing the sent/received file
         */
        var subj = new Subject ();
        subj.uri = channel.file.get_uri ();
        subj.interpretation = interpretation_for_mimetype (info.get_content_type ());
        subj.manifestation = NFO.FILE_DATA_OBJECT;
        subj.text = info.get_display_name ();
        subj.mimetype = info.get_content_type ();
        if (channel.requested == true)
        {
          var split_uri = channel.file.get_uri ().split ("/");
          var uri = "%s/".printf(string.join ("/", split_uri[0:split_uri.length-1]));
          subj.origin = uri;
        }
        else
          subj.origin = tp_identifier.printf (target.get_identifier ());
        event_template.add_subject (subj);

        /*
         * Create Subject representing contact received from or sent to
         */
        event_template.add_subject (
          new Subject.full (tp_identifier.printf(target.get_identifier ()),
            NCO.CONTACT,
            NCO.CONTACT_LIST_DATA_OBJECT,
            "",
            obj_path,
            target.get_alias (),
            "net"));
        /*
         * Create Payload
         */
        var gen = new Generator();
        var root = new Json.Node(NodeType.OBJECT);
        var object = new Json.Object();
        root.set_object(object);
        gen.set_root(root);
        gen.pretty = true;
        var details_obj = new Json.Object ();
        TelepathyGLib.FileTransferStateChangeReason reason;
        var state = channel.get_state (out reason);
        details_obj.set_int_member ("state", state);
        details_obj.set_int_member ("reason", reason);
        details_obj.set_boolean_member ("requested", channel.requested);
        details_obj.set_string_member ("description", channel.get_description ());
        details_obj.set_double_member ("size", (int64)channel.get_size ());
        details_obj.set_string_member ("service", channel.get_service_name ());
        size_t length;
        object.set_object_member (ft_json_domain, details_obj);
        string payload_string = gen.to_data (out length);
        event_template.payload = new GLib.ByteArray.take (payload_string.data);
        this.push_event (event_template);
      }
  }

  private void observe_ft_channel (SimpleObserver observer, Account account,
                                   Connection connection, Channel b_channel,
                                   ChannelDispatchOperation? dispatch_operation,
                                   List<ChannelRequest> requests,
                                   ObserveChannelsContext context)
  {
    FileTransferChannel channel = (FileTransferChannel) b_channel;
    channel.notify["state"].connect (() => {
        this.handle_ftchannel_change.begin (observer, account, connection, channel,
          dispatch_operation, requests, context);
      });
  }

  private void observe_channels (SimpleObserver observer, Account account,
                                 Connection connection, List<Channel> channels,
                                 ChannelDispatchOperation? dispatch_operation,
                                 List<ChannelRequest> requests,
                                 ObserveChannelsContext context)
  {
    try
    {
      foreach (var channel in channels)
      {
        if (channel is TelepathyGLib.TextChannel)
          this.observe_text_channel (observer, account, connection, channel,
                            dispatch_operation, requests, context);
        else if (channel is TelepathyGLib.CallChannel)
          this.observe_call_channel (observer, account, connection, channel,
                            dispatch_operation, requests, context);
        else if (channel is TelepathyGLib.FileTransferChannel)
          this.observe_ft_channel (observer, account, connection, channel,
                            dispatch_operation, requests, context);
      }
    }
    finally
    {
      context.accept ();
    }
  }

  public override void start ()
  {
    observer = new TelepathyGLib.SimpleObserver.with_factory (factory,
                                                              true,
                                                              "Zeitgeist",
                                                              false,
                                                              observe_channels);
    /*
     * Add Call Channel Filters
     */
    HashTable<string,Value?> call_filter = new HashTable<string,Value?> (str_hash, str_equal);
    call_filter.insert (TelepathyGLib.PROP_CHANNEL_CHANNEL_TYPE,
                        TelepathyGLib.IFACE_CHANNEL_TYPE_CALL);
    call_filter.insert (TelepathyGLib.PROP_CHANNEL_TARGET_HANDLE_TYPE, 1); // 1 => TP_HANDLE_TYPE_CONTACT, somehow vala fails to compile when using the constant
    observer.add_observer_filter (call_filter);
    /*
     * Add Text Channel Filters
     */
    HashTable<string,Value?> text_filter = new HashTable<string,Value?> (str_hash, str_equal);
    text_filter.insert (TelepathyGLib.PROP_CHANNEL_CHANNEL_TYPE,
                        TelepathyGLib.IFACE_CHANNEL_TYPE_TEXT);
    text_filter.insert (TelepathyGLib.PROP_CHANNEL_TARGET_HANDLE_TYPE, 1); // 1 => TP_HANDLE_TYPE_CONTACT, somehow vala fails to compile when using the constant
    observer.add_observer_filter (text_filter);
    /*
     * Add FileTransfer Channel Filters
     */
    HashTable<string,Value?> ft_filter = new HashTable<string,Value?> (str_hash, str_equal);
    ft_filter.insert (TelepathyGLib.PROP_CHANNEL_CHANNEL_TYPE,
                      TelepathyGLib.IFACE_CHANNEL_TYPE_FILE_TRANSFER);
    ft_filter.insert (TelepathyGLib.PROP_CHANNEL_TARGET_HANDLE_TYPE, 1); // 1 => TP_HANDLE_TYPE_CONTACT, somehow vala fails to compile when using the constant
    observer.add_observer_filter (ft_filter);
    try
    {
      observer.register ();
    }
    catch (GLib.Error err)
    {
      warning ("Couldn't register observer: %s", err.message);
    }
  }

  public override void stop ()
  {
    observer.unregister ();
  }
}
