               'assistant_message': {
                   'id': assistant_message.id,
                   'role': assistant_message.role,
                   'content': assistant_message.content,
                   'timestamp': assistant_message.timestamp.isoformat()
               }
           })
   except ConversationError as e:
       return jsonify({
           'error': 'Conversation not found',
           'details': str(e),
           'code': 'NOT_FOUND'
       }), 404
   except Exception as e:
       logger.error(f"Error adding message: {str(e)}", exc_info=True)
       return jsonify({
           'error': 'Server Error',
           'details': str(e),
           'code': 'SERVER_ERROR'
       }), 500
