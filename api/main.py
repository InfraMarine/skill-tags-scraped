from flask import Flask, Request
from flask.globals import request
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)

### MODELS ###

class SiteModel(db.Model):
	__tablename__ = 'site'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	tags = db.relationship("TagModel", back_populates="site")

class TagModel(db.Model):
	__tablename__ = 'tag'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	count = db.Column(db.Integer, nullable=False)
	site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)
	site = db.relationship("SiteModel", back_populates="tags")


### KINDA SCHEMA ###

tag_parser = reqparse.RequestParser()
tag_parser.add_argument("name", type=str, help="Name of the tag is required", required=True)
tag_parser.add_argument("count", type=int, help="Occurances of the tag is required", required=True)
tag_parser.add_argument("site_id", type=int, help="Origin site id is required", required=True)

site_parser = reqparse.RequestParser()
site_parser.add_argument("name", type=str, help="Name of the resource is required", required=True)

tag_fields = {
	'id': fields.Integer,
	'name': fields.String,
	'count': fields.Integer,
	'site_id': fields.Integer,
	'site_name': fields.String(attribute='site.name'),
}

site_fields = {
	'id': fields.Integer,
	'name': fields.String
}


### VIEWS ###

class Site(Resource):
	@marshal_with(site_fields)
	def get(self, site_id=None):
		if not site_id:
			return SiteModel.query.all()
		site = SiteModel.query.get_or_404(id=site_id)
		return site

	@marshal_with(site_fields)
	def put(self):
		args = site_parser.parse_args()
		site = SiteModel.query.filter_by(name=args['name']).first()
		if site:
			return site, 409
		site = SiteModel(name=args['name'])
		db.session.add(site)
		db.session.commit()
		return site, 201

	def delete(self,site_id=None):
		q = SiteModel.query
		if site_id:
			q = q.get_or_404(id=site_id)
		count = q.delete()
		db.session.commit()
		return f'{count} origin sites deleted', 204


class Tag(Resource):
	@marshal_with(tag_fields)
	def get(self, site_id=None):
		# parsing param to get top N results
		top_arg = request.args.get('top')

		if not site_id:
			return TagModel.query.all()
		site = SiteModel.query.get_or_404(site_id)
		que = TagModel.query.filter_by(site_id=site.id)
		
		if top_arg:
			que = que.order_by(TagModel.count.desc()).limit(int(top_arg))	
		return que.all()

	@marshal_with(tag_fields)
	def put(self):
		args = tag_parser.parse_args()
		SiteModel.query.get_or_404(args['site_id'])
		tag = TagModel(name=args['name'], count=args['views'], site_id=args['site.id'])
		db.session.add(tag)
		db.session.commit()
		return tag, 201

	def post(self, site_id):
		dict = request.get_json()
		site = SiteModel.query.filter_by(id=site_id).first()
		if not site:
			abort(404, message="No site with such id")
		tags = [TagModel(name=k, count=v, site_id=site.id) for k,v in dict.items()]
		db.session.add_all(tags)
		db.session.commit()
		tags_count = len(tags)
		return f"{tags_count} tags added", 201

	def delete(self, site_id=None):
		q = TagModel.query
		if site_id:
			site = SiteModel.query.get_or_404(site_id)
			q = q.filter_by(site_id=site.id)
		count = q.delete()
		db.session.commit()
		return f"{count} tags deleted", 200

api.add_resource(Site, "/site", "/site/<site_id>")
api.add_resource(Tag, "/tag", "/tag/<site_id>")

if __name__ == "__main__":
	db.create_all()
	app.run(debug=True, host 0.0.0.0)
