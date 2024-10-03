from slack import WebClient
import logging
#depends on slackclient 2.9.4
import yaml

class slacknotificationmanager:
    def __init__(self, bot, apiKey):
        self.bot = bot
        self.api_key = apiKey

    def slackAlert_mrkdwn(self, msg, SLACK_CHANNEL, thread_ts=''):
        slackClient = WebClient(token=self.api_key)
        thread = slackClient.chat_postMessage(channel=SLACK_CHANNEL,
                                              thread_ts=thread_ts,
                                              blocks=[{
                                                  "type": "section",
                                                  "text": {
                                                      "type": "mrkdwn",
                                                      "text": f"```{msg}```"
                                                  }
                                              }]
                                              )
        return (thread)

    def slackAlert_mrkdwn_batchedshow(self, df, SLACK_CHANNEL, thread_ts=''):
        df.reset_index(inplace=True, drop=True)
        slackClient = WebClient(token=self.api_key)
        i = 0
        displayBatchSize = 30
        totalMsgSize = int(df.shape[0])

        while (i < totalMsgSize):
            start = i
            end = start + displayBatchSize
            if end > totalMsgSize : end = totalMsgSize

            msg = df.loc[start:end].to_string(index=False)
            slackClient.chat_postMessage(channel=SLACK_CHANNEL,
                                                  thread_ts=thread_ts,
                                                  blocks=[{
                                                      "type": "section",
                                                      "text": {
                                                          "type": "mrkdwn",
                                                          "text": f"```{msg}```"
                                                      }
                                                  }])
            i += (displayBatchSize + 1)
        return

    def slackAlert(self, msg, SLACK_CHANNEL, thread_ts=''):
        slackClient = WebClient(token=self.api_key)
        thread = slackClient.chat_postMessage(channel=SLACK_CHANNEL, thread_ts=thread_ts, text=msg)['ts']
        return (thread)

    def slackAlertV2(self, msg, SLACK_CHANNEL, thread_ts=''):
        #this function same with slackAlert() except that it addtionally print to console/loki
        slackClient = WebClient(token=self.api_key)
        thread = slackClient.chat_postMessage(channel=SLACK_CHANNEL, thread_ts=thread_ts, text=msg)['ts']
        print(msg)
        return (thread)


    def slackAlertAndLog(self, loglevel, msg, SLACK_CHANNEL, thread_ts=''):
        if loglevel=="info": logging.info(msg)
        elif loglevel=="error": logging.error(msg)
        else: return

        slackClient = WebClient(token=self.api_key)
        thread = slackClient.chat_postMessage(channel=SLACK_CHANNEL, thread_ts=thread_ts, text=msg)['ts']
        return (thread)


#Testing
# with open("D:\TPProjects\i40nervecentre\i40ncConfig.yml") as cfgfile:
#     config = yaml.load(cfgfile, Loader=yaml.FullLoader)
#
#     slackConfig = config["Slack"]
#     snm = slacknotificationmanager("",slackConfig["oAuth"])
#     snm.slackAlert("testing!!!", slackConfig["channel"])

# snm = slacknotificationmanager("", "mm_alert")
# snm.slackAlert("testing!!!","test_bot")