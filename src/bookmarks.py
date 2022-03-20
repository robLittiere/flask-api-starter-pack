from flask import Blueprint, jsonify, request
import validators
from src.constants.http_status_code import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from src.models.Bookmark import Bookmark
from flask_jwt_extended import get_jwt_identity, jwt_required
from src.database import db
from flasgger import Swagger, swag_from

bookmarks = Blueprint("bookmark", __name__, url_prefix="/api/v1/bookmarks")


@bookmarks.route("/", methods=['GET', 'POST'])
@jwt_required()
def get_all():
    current_user_id = get_jwt_identity()
    if request.method == 'POST':
        body = request.get_json().get('body', '')
        url = request.get_json().get('url', '')

        if not validators.url(url):
            return jsonify({
                'error' : "Enter a valid url"
            }), HTTP_400_BAD_REQUEST
    
        if Bookmark.query.filter_by(url=url).first():
            return jsonify({
                'error' : 'URL already exists'
            }), HTTP_400_BAD_REQUEST

        bookmark=Bookmark(url=url, body=body, user_id=current_user_id)

        # Add to db
        db.session.add(bookmark)
        db.session.commit()

        return jsonify({
            'body': bookmark.body,
            'id' : bookmark.id,
            'url': bookmark.url,
            'short_url' : bookmark.short_url,
            'visits': bookmark.visits,
            'created_at': bookmark.created_at,
            'updated_at': bookmark.updated_at
        }), HTTP_201_CREATED
    
    if request.method == 'GET': 
        # Add pagination variable through request object
        page=request.args.get('page', 1, type=int)
        per_page=request.args.get('per_page', 5, type=int)

        # Returns a pagination object 
        # https://flask-sqlalchemy.palletsprojects.com/en/2.x/api/#flask_sqlalchemy.Pagination
        bookmarks=Bookmark.query.filter_by(user_id=current_user_id).paginate(page=page, per_page=per_page)

        data = []
        # Bookmark.items contient le retour de la bd, donc notre data
        for bookmark in bookmarks.items:
            data.append({
                'body': bookmark.body,
                'id' : bookmark.id,
                'url': bookmark.url,
                'short_url' : bookmark.short_url,
                'visits': bookmark.visits,
                'created_at': bookmark.created_at,
                'updated_at': bookmark.updated_at
            })
        # On peut aussi récupérer pas mal d'élément en plus
        meta={
            "page": bookmarks.page,
            "pages": bookmarks.pages,
            "total_count": bookmarks.total,
            "prev_page": bookmarks.prev_num,
            "next_page": bookmarks.next_num,
            "has_next": bookmarks.has_next,
            "has_prev": bookmarks.has_prev,

        }   
        return jsonify({
            "data": data,
            "meta": meta
        }), HTTP_200_OK


@bookmarks.get("/<int:id>")
@jwt_required()
def get_bookmark(id):
    current_user_id = get_jwt_identity()
    bookmark = Bookmark.query.filter_by(user_id = current_user_id, id = id).first()

    if not bookmark:
        return jsonify({'message' : 'Item not found'}), HTTP_404_NOT_FOUND

    
    return jsonify({
        'body': bookmark.body,
        'id' : bookmark.id,
        'url': bookmark.url,
        'short_url' : bookmark.short_url,
        'visits': bookmark.visits,
        'created_at': bookmark.created_at,
        'updated_at': bookmark.updated_at
    }), HTTP_200_OK

# Double handler, handles put and patch methods
@bookmarks.put("/<int:id>")
@bookmarks.patch("/<int:id>")
@jwt_required()
def modify_bookmark(id):
    current_user_id = get_jwt_identity()
    bookmark = Bookmark.query.filter_by(user_id = current_user_id, id = id).first()

    if not bookmark:
        return jsonify({'message' : 'Item not found'}), HTTP_404_NOT_FOUND

    
    body = request.get_json().get('body', '')
    url = request.get_json().get('url', '')

    if not validators.url(url):
        return jsonify({
            'error' : "Enter a valid url"
        }), HTTP_400_BAD_REQUEST

    # Modify the bookmark we got back
    bookmark.url = url
    bookmark.body = body
    db.session.commit()

    return jsonify({
        'body': bookmark.body,
        'id' : bookmark.id,
        'url': bookmark.url,
        'short_url' : bookmark.short_url,
        'visits': bookmark.visits,
        'created_at': bookmark.created_at,
        'updated_at': bookmark.updated_at
    }), HTTP_200_OK


@bookmarks.delete("/<int:id>")
@jwt_required()
def delete_bookmark(id):
    current_user_id = get_jwt_identity()
    bookmark = Bookmark.query.filter_by(user_id = current_user_id, id = id).first()

    if not bookmark:
        return jsonify({'message' : 'Item not found'}), HTTP_404_NOT_FOUND

    db.session.delete(bookmark)
    db.session.commit()
    return jsonify({}), HTTP_204_NO_CONTENT

    
@bookmarks.get("/stats")
@jwt_required()
@swag_from('./docs/bookmarks/stats.yaml')
def get_stats():
    data = []
    current_user_id = get_jwt_identity()

    items = Bookmark.query.filter_by(user_id=current_user_id).all()

    for item in items:
        new_link = {
            'visits' : item.visits,
            'url' : item.url,
            'short_url' : item.short_url,
            'id' : item.id,
        }
        data.append(new_link)
    
    return jsonify({
        "data" : data
    }), HTTP_200_OK