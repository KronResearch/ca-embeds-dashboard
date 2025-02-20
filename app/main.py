from fasthtml.common import *
from monsterui.all import *
from fasthtml.svg import *
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Initialize Supabase client
load_dotenv()
url: str = os.environ.get("SUPABASE_PUBLIC_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

# First authenticate with Supabase
response = supabase.auth.sign_in_with_password(
    {
        "email": os.getenv("SUPABASE_EMAIL"),
        "password": os.getenv("SUPABASE_PASSWORD"),
    }
)

# Helper functions from the notebook
def list_folders(path):
    return L(supabase.storage
        .from_("embeddings")
        .list(
            str(path),
            {
                "offset": 0,
                "sortBy": {"column": "name", "order": "desc"},
            }
        )
    )

def get_public_url(path):
    return supabase.storage.from_("embeddings").get_public_url(path)

# Create FastHTML app with MonsterUI theme
app, rt = fast_app(hdrs=Theme.blue.headers())

@rt("/")
def get():
    data_path = 'remote/data/downloads/archives'
    embed_folders = list_folders(data_path)
    embed_names = [f['name'] for f in embed_folders]

    return Title("Embeddings Dashboard"), Container(
        # Header section
        H2('Embeddings Explorer'),

        # Main content grid
        Grid(
            # Left sidebar with model selection
            Card(
                H3("Available Models"),
                NavContainer(*[
                    Li(A(name,
                         href=f"/model/{name}",
                         hx_get=f"/model/{name}",
                         hx_target="#model-content"))
                    for name in embed_names
                ], cls=NavT.primary),
                cls='col-span-1'
            ),

            # Main content area
            Card(
                H3("Select a model to view users"),
                id="model-content",
                cls='col-span-3'
            ),
            cols=4,
            gap=4
        ),
        cls=ContainerT.xl
    )

@rt("/model/{model_name}")
def get(model_name: str):
    data_path = 'remote/data/downloads/archives'

    # Get files and group by user
    embed_files = list_folders(f'{data_path}/{model_name}').filter(lambda o: '_shard_' in o['name'])
    npy_files = embed_files.filter(lambda o: o['name'].endswith('.npy'))
    uniq_users = npy_files.map(lambda x: x['name'].split('_embeddings_')[0]).sorted().unique()

    grouped_files = {
        u: embed_files.filter(lambda o: u in o['name'])
        for u in uniq_users
    }

    return Card(
        H3(f"Users for {model_name}"),
        # User list with expandable details
        *[Card(
            DivFullySpaced(
                H4(user),
                Button("View Files",
                      data_uk_toggle=f"target: #files-{user}",
                      cls=ButtonT.primary)
            ),
            Div(
                *[DivLAligned(
                    UkIcon('file'),
                    A(f.get('name'),
                      href=get_public_url(f"{data_path}/{model_name}/{f.get('name')}"),
                      cls=TextT.muted)
                ) for f in grouped_files[user]],
                id=f"files-{user}",
                hidden=True,
                cls='space-y-2 mt-4'
            ),
            cls=CardT.hover
        ) for user in uniq_users],
        cls='space-y-4'
    )

serve()
