
// See server-side protocol definition for detailed description of fields
var Protocol = {
    LOGIN: 'login',
    LOGIN_FAILED: 'login_failed',
    LOGOUT: 'logout',
    LOGOUT_FAILED: 'logout_failed',
    PUBLIC_MESSAGE: 'public_message',
    PRIVATE_MESSAGE: 'private_message',
    LIST_ALL_USERS: 'list_all_users'
};

var Message = function(messageType, senderUserName, messageText, receiverUserName, allUsers) {
    return {
        messageType: messageType,
        senderUserName: senderUserName,
        messageText: messageText,
        receiverUserName: receiverUserName,
        allUsers: allUsers
    }
};

var ChatServer = function(chatView) {
    var self = this;
    self.wsConnection;
    self.chatView = chatView;
    self.userName = '';
    self.isLoggedIn = false;

    self.init = function() {
        var url = 'ws://' + location.host + '/websocket';
        self.wsConnection = new WebSocket(url);

        self.wsConnection.onmessage = function (event) {
            self.handleMessageFromServer(JSON.parse(event.data));
        };
    };

    self.handleMessageFromServer = function(msg) {
        switch (msg.messageType) {
            case Protocol.LOGIN:
                if (msg.senderUserName == self.userName) {
                    self.isLoggedIn = true;
                }
                self.chatView.renderUserLogin(msg.senderUserName);
                break;
            case Protocol.LOGIN_FAILED:
                self.chatView.renderUserLoginFailed(msg.messageText);
                break;
            case Protocol.LOGOUT:
                self.isLoggedIn = false;
                self.chatView.renderUserLogout(msg.senderUserName);
                break;
            case Protocol.LOGOUT_FAILED:
                self.chatView.renderUserLogoutFailed(msg.messageText);
                break;
            case Protocol.PUBLIC_MESSAGE:
                self.chatView.renderPublicMessage(msg.senderUserName, msg.messageText);
                break;
            case Protocol.PRIVATE_MESSAGE:
                self.chatView.renderPrivateMessage(msg.senderUserName, msg.receiverUserName, msg.messageText, msg.senderUserName != self.userName);
                break;
            case Protocol.LIST_ALL_USERS:
                self.chatView.renderAllUsers(msg.allUsers);
                break;
            default: // unknown command
                ;
        }
    };

    self.parseUserQueryAndSendMessageToServer = function(userQuery) {
        var tokens = userQuery.split(' ');
        var messageType = tokens[0];
        if (!self.isLoggedIn) {
            if (messageType == 'login') {
                self.userName = tokens[1];
                self.sendAsText(new Message(Protocol.LOGIN, self.userName));
            }
            else {
                self.chatView.addAsListItem('not yet logged in');
            }
        }
        else {
            switch (messageType) {
                case 'login':
                    self.chatView.addAsListItem('already logged in');
                case 'logout':
                    self.sendAsText(new Message(Protocol.LOGOUT, self.userName));
                    break;
                case 'public':
                    var messageText = tokens.slice(1).join(' ');
                    self.sendAsText(new Message(Protocol.PUBLIC_MESSAGE, self.userName, messageText));
                    break;
                case 'private':
                    var receiver = tokens[1];
                    var messageText = tokens.slice(2).join(' ');
                    self.sendAsText(new Message(Protocol.PRIVATE_MESSAGE, self.userName, messageText, receiver));
                    break;
                case 'listall':
                    self.sendAsText(new Message(Protocol.LIST_ALL_USERS, self.userName));
                    break;
                default: // unknown command
                    ;
            }
        }
    };

    self.sendAsText = function(object) {
        self.wsConnection.send(JSON.stringify(object));
    };
};

var ChatView = {
    el: $('#messagesBox ul'),
    addAsListItem: function(html) {
        this.el.append('<li>' + html + '</li>');
    },
    renderBold: function(userName) {
        return '<span class="userName">' + userName + '</span>'
    },
    renderUserLogin: function(userName) {
        this.addAsListItem(this.renderBold(userName) + ' joined the chat');
    },
    renderUserLoginFailed: function(messageText) {
        this.addAsListItem('login failed: ' + messageText);
    },
    renderUserLogout: function(userName) {
        this.addAsListItem(this.renderBold(userName) + ' has left the chat');
    },
    renderUserLogoutFailed: function(messageText) {
        this.addAsListItem('logout failed: ' + messageText);
    },
    renderPublicMessage: function(userName, messageText) {
        this.addAsListItem(this.renderBold(userName) + ': ' + messageText);
    },
    renderPrivateMessage: function(senderUserName, receiverUserName,  messageText, isReceivedMessage) {
        if (isReceivedMessage)
            var description = 'private message from ' + this.renderBold(senderUserName);
        else
            var description = 'private message to ' + this.renderBold(receiverUserName);
        this.addAsListItem(description + ': '+ messageText)
    },
    renderAllUsers: function(users) {
        var usersHtml = $.map(users, function(userName) {
            return ChatView.renderBold(userName)
        });
        this.addAsListItem('current users: ' + usersHtml.join(', '));
    },
    renderHelpText: function() {
        this.addAsListItem('Chat commands available:<br>');
        this.addAsListItem('-------------------------------------------<br>');
        this.addAsListItem(this.renderBold('login &lt;user name&gt;') + ': required to participate in chat<br>');
        this.addAsListItem(this.renderBold('logout') + ': leaves the chat<br>');
        this.addAsListItem(this.renderBold('public &lt;message&gt;') + ': sends message to all users<br>');
        this.addAsListItem(this.renderBold('private &lt;receiver user name&gt &lt;message&gt;') + ': sends private message to specified user<br>');
        this.addAsListItem(this.renderBold('listall') + ': lists all users<br>');
        this.addAsListItem('-------------------------------------------<br><br>');
    }
};

$(document).ready(function() {
    var chatServer = new ChatServer(ChatView);
    chatServer.init();
    $('form').submit(function(event) {
        event.preventDefault();
        var userQuery = $('#query', $(this)).val();
        console.log(userQuery);
        chatServer.parseUserQueryAndSendMessageToServer(userQuery);
    });
    $('form #query').focus();
    ChatView.renderHelpText();
});